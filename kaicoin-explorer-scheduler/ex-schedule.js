var schedule = require('node-schedule');
var https = require('https');
var svc = require('./nodejs/schedule-service')();

var ticker, price, row;

var reqTicker = {
	hostname: 'stocks.exchange',
	port: '443',
	path: '/api2/ticker'
};
var reqPrice = {
	hostname: 'stocks.exchange',
	port: '443',
	path: '/api2/prices'
};

// Runs every 2min
var j = schedule.scheduleJob('*/2 * * * *', function(){
    // Get ticker for Chart data
	var now = new Date();
	var min = now.getMinutes();
	console.log('scheduler runs at ' + min + 'min');
	// 1) Ticker call -> 2) Price call
	https.request(reqTicker, function(response){
		onTicker(response);
	}).end();
});

// 1) Prices
// {"buy":"0.00003","sell":"0.000031","market_name":"ARDOR_BTC","updated_time":1520612402,"server_time":1520612402}
// 2) Ticker
// {"min_order_amount":"0.00000010","ask":"0.00013238","bid":"0.0000976","last":"0.00013238","lastDayAgo":"0.00014953",
//	"vol":"10.3","spread":"0","buy_fee_percent":"0","sell_fee_percent":"0","market_name":"STEX_BTC",
//	"updated_time":1520613001,"server_time":1520613001}
function onTicker(response) {
    var serverData = '';
    ticker = null;
    response.on('data', function (chunk) {
        serverData += chunk;
    });
    response.on('end', function () {
        var data;
        try {
            data = JSON.parse(serverData);
        } catch (e) { console.warn('no json response, ' + e.message); return; }
        for (var i=0; i<data.length; i++) {
            var datum = data[i];
            if (datum.market_name=='KAI_BTC') {
                console.log('got ticker');
                ticker = datum;
                break;
            }
        }
        https.request(reqPrice, function(response2){
            onPrice(response2);
        }).end();
    });
}

function onPrice(response) {
    var serverData = '';
    price = null;
    response.on('data', function (chunk) {
        serverData += chunk;
    });
    response.on('end', function () {
        try {
            data = JSON.parse(serverData);
        } catch (e) { console.warn('no json response, ' + e.message); return; }
        for (var i=0; i<data.length; i++) {
            var datum = data[i];
            if (datum.market_name=='KAI_BTC') {
                console.log('got price');
                price = datum;
                row = Object.assign({}, ticker, price);
                break;
            }
        }
        console.log('merged datum ' + JSON.stringify(row));
        svc.insertPrice(row);
    });
}

// 현재 미사용, 참고용
/*
 * Connect to rethinkdb, create the needed tables/indexes and then start express.
 * Create tables/indexes then start express
 */
// async.waterfall([
//     function connect(callback) {
//         r.connect(config.rethinkdb, callback);
//     },
//     function createDatabase(connection, callback) {
//         //Create the database if needed.
//         r.dbList().contains(config.rethinkdb.db).do(function(containsDb) {
//             return r.branch(
//                 containsDb,
//                 {created: 0},
//                 r.dbCreate(config.rethinkdb.db)
//             );
//         }).run(connection, function(err) {
//             callback(err, connection);
//         });
//     },
//     function createTable(connection, callback) {
//         //Create the table if needed.
//         r.tableList().contains('todos').do(function(containsTable) {
//             return r.branch(
//                 containsTable,
//                 {created: 0},
//                 r.tableCreate('todos')
//             );
//         }).run(connection, function(err) {
//             callback(err, connection);
//         });
//     },
//     function createIndex(connection, callback) {
//         //Create the index if needed.
//         r.table('todos').indexList().contains('createdAt').do(function(hasIndex) {
//             return r.branch(
//                 hasIndex,
//                 {created: 0},
//                 r.table('todos').indexCreate('createdAt')
//             );
//         }).run(connection, function(err) {
//             callback(err, connection);
//         });
//     },
//     function waitForIndex(connection, callback) {
//         //Wait for the index to be ready.
//         r.table('todos').indexWait('createdAt').run(connection, function(err, result) {
//             callback(err, connection);
//         });
//     }
// ], function(err, connection) {
//     if(err) {
//         console.error(err);
//         process.exit(1);
//         return;
//     }
// });