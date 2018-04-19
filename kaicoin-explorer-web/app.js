'use strict'

const fastify = require('fastify')();
const path = require('path');
const resolve = path.resolve;
const service = require("./nodejs/web-service")();
const plugin = require("./nodejs/plugin");
const SocketIo = require('socket.io');
const r = require('rethinkdb');
const config = require('./nodejs/config');
const templatesFolder = 'views';
const socketEvents = require('./nodejs/socket-handler.js');

fastify.register(require('fastify-static'), {
    root: path.join(__dirname, 'public'),
    prefix: '/res/'
});

fastify.register(plugin, {
    engine: { ejs: require('ejs') },
    includeViewExtension: true,
    templates: templatesFolder,
    options: { filename: resolve(templatesFolder) },
    // sample usage, but specifying the same value already used as default
    charset: 'utf-8'
});

fastify.get('/', (req, reply) => {
    service.connectDB().then(conn =>
        service.getSummary(conn).then(res1 => {
            service.getBlocks(conn, LIST_COUNT_MAIN).then(res2 => {
                service.getTxs(conn, LIST_COUNT_MAIN).then(res3 => {
                    service.disconnectDB(conn);
                    reply.view('index', {summary: res1, blocks: res2, txs: res3});
                });
            });
        })
    );
});

fastify.get('/summary', (req, reply) => {
    service.connectDB().then(conn => {
        service.getSummary(conn).then(res1 => {
            let date = new Date();
            date.setTime(res1["genesis-timestamp"]*1000);
            res1["genesis-datetime"] = date.format("yyyy.MM.dd HH:mm:ss");
            reply.view('summary', {item: res1});
        }, function(e) {
            console.error('failed to connect to blockchain' + e);
        });
    });
});

/**
 * 검색 64자는
 * 1) 블록해시 000000000fcd910cf007d3c3ddcd94cc9d30b72029f1c5114b7a144f97a42cbb
 * 2) TX해시 a4dc6969669519d1abfd2d4f051a9f2200c981a915cedd271d300ef30e4c6f13
 *      => 블록해시 00000000 현재 0*8개
 * 3) 1로 시작하고 38자는 주소 1D2WDbRBJzYHF9tRmyE2eCDixzuWJvacKZw1Pk
 * 4) 정수 10자 이내는 블록 높이
 */
fastify.get('/q/:q', (req, reply) => {
    const param = req.params.q;
    let json = reply.code(200).header('Content-Type', 'application/json');
    if (param.length>64) {
        json.send({type: null});
    } else {
        const alphanumeric = /^[0-9a-zA-Z]+$/;
        if(param.match(alphanumeric)===false) {
            json.send({type: null});
        } else {
            if (param.length===64) {
                if (param.startsWith('0000')) {
                    // 블록해시 (추정)
                    json.send({type: 'block'});
                } else {
                    // TX 해시
                    json.send({type: 'tx'});
                }
            } else if (param.length===38) {
                // 주소
                json.send({type: 'address'});
            } else if (param.length<10) {
                // 블록 높이
                const numeric = /^\d+$/;
                if(param.match(numeric)===false) {
                    json.send({type: null});
                } else {
                    json.send({type: 'block'});
                }
            } else {
                json.send({type: 'none'});
            }
        }
    }
});

fastify.get('/blocks', (req, reply) => {
    service.connectDB().then(conn => {
        service.getSummary(conn).then(res1 => {
            service.getBlocks(conn, LIST_COUNT_PER_PAGE).then(res2 => {
                let result = {summary: res1, list: res2};
                console.log('result ' + JSON.stringify(result));
                reply.view('blocks', result);
            }, function(e) {
                console.error('failed to connect to blockchain' + e);
            });
        }, function(e) {
            console.error('failed to connect to blockchain' + e);
        });
    });
});

fastify.get('/block/:bhash', (req, reply) => {
    service.getBlock(req.params.bhash).then(res1 => {
        console.log('item ' + JSON.stringify(res1));
        reply.view('block', {q: req.params.bhash, item: res1});
    }, function(e) {
        console.error('failed to connect to blockchain' + e);
    });
});

// address => TX list
fastify.get('/address/:address', (req, reply) => {
    // service.connectDB().then(conn => {
    //     service.getSummary(conn).then(res1 => {
    //         service.getBlocks(conn, res1).then(res2 => {
    //             // console.log('list ' + JSON.stringify(res2));
    //             let result = {summary: res1, list: res2};
    //             reply.view('address', result);
    //         }, function(e) {
    //             console.error('failed to connect to blockchain' + e);
    //         });
    //     }, function(e) {
    //         console.error('failed to connect to blockchain' + e);
    //     });
    // });
    reply.view('address', {});
});

// TXS: getmempoolinfo + BLOCKS + BLOCK + TXS + TX
fastify.get('/txs', (req, reply) => {
    service.connectDB().then(conn => {
        service.getSummary(conn).then(res1 => {
            service.getTxs(conn, LIST_COUNT_PER_PAGE).then(res2 => {
                service.disconnectDB(conn);
                console.log('res2 ' + JSON.stringify(res2));
                let result = {summary: res1, list: res2};
                reply.view('txs', result);
            });
        }, function(e) {
            console.error('failed to connect to blockchain' + e);
        });
    });
});

fastify.get('/tx/:txid', (req, reply) => {
    // 1. 공통
    // 1) 공통응답: blockhash, confirmations, time, blocktime, hex, txid, version, locktime
    // 2) 금액 있는 건: vout[n].type = 'pubkeyhash'

    // 2. 마이닝
    // 1) vin[[=0?]]: coinbase, sequence
    // 2) vout[n]: n, value, scriptPubKey(asm, hex, type[=nulldata]), data[]
    // 2) vout[0]의 value, scriptPubKey.addresses[0]만 체크하면 될까..?

    // 3. 전송
    // 1) vin[]: txid(조각들의..), vout[=0], scriptSig(asm, hex), sequence
    // 2) vout[n]: n, value, scriptPubKey(asm, hex, type[=pubkeyhash], reqSigs, addresses[])
    // 2) vout[0].scriptPubKey.addresses: 수신자
    // 2) vout[1].scriptPubKey.addresses: 전송자
    service.getRawTx(req.params.txid).then(res1 => {
        reply.view('tx', {item: res1});
    }, function(e) {
        console.error('failed to handle getRawTx ' + e);
    });
});

/**
 * for backward compatibility
 */
fastify.get('/MultiChain%20kaicoin/tx/:txid', (req, reply) => {
    reply.redirect('/tx/' + req.params.txid);
});


// listblocks block heights, hashes, height ranges (e.g. 100-200) or -n
// for the most recent n blocks. Alternatively, pass an object {"starttime":...,"endtime":...}
fastify.listen(3000, err => {
    if (err) throw err;
    console.log(`server listening on ${fastify.server.address().port}`);
    let io = SocketIo(fastify.server); // socket.io와 서버 연결
    io.origins('*:*');
    handleRealtime(io);
});

let connected_user = [];
let msocket = null;

function handleRealtime(io) {

    io.on('connection', function (socket) {
        console.log('io connection req ' + socket.id);
        connected_user.push(socket.id);
        msocket = socket;
        socket.emit('message', {'stat': 'connection'});
        socket.on('message', function(data) {
            console.log('io message req ' + JSON.stringify(data));
            socket.emit('message', {'name': "i'm server"});
        });
        socket.on('disconnect', function(user) {
            console.log('disconnect ' + JSON.stringify(user));
            // connected_user.pop(socket.id);
            // if (connected_user.id !== undefined) {
            //     delete usersonline[connected_user.id];
            //     console.log("[DEBUG][io.sockets][disconnect] user: %s(@%s) disconnected", connected_user.username, connected_user.id);
            // } else {
            //     console.log("[WARN][io.sockets][disconnect] Received disconnect message from another universe");
            // }
        });
    });
    // socket.broadcast.emit('us', {'msg': 'hi message'});
    r.connect(rethinkdb, function(e, conn) {
        if (e) {
            console.warn("could not connect to the database, " + e.message);
            if (conn) { conn.close(); }
            return;
        }
        console.log("realtime handler");
        // r.table(table.TB_SUMMARY).get('kaicoin').changes().run(conn).then(function(cur1){
        r.table(table.TB_SUMMARY).changes().run(conn, function(err, cur1) {
            console.log('table changes() ' + msocket);
            if (msocket===null) { return; }
            cur1.each(function(err, row) {
                if (err) throw err;
                console.log('changed ' + JSON.stringify(row));
                msocket.broadcast.emit('message', {changed: row});
            });
        });
    });
}

Date.prototype.format = function(f) {
    if (!this.valueOf()) return " ";

    var weekName = ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"];
    var d = this;

    return f.replace(/(yyyy|yy|MM|dd|E|hh|mm|ss|a\/p)/gi, function($1) {
        var h;
        switch ($1) {
            case "yyyy": return d.getFullYear();
            case "yy": return (d.getFullYear() % 1000).zf(2);
            case "MM": return (d.getMonth() + 1).zf(2);
            case "dd": return d.getDate().zf(2);
            case "E": return weekName[d.getDay()];
            case "HH": return d.getHours().zf(2);
            case "hh": return ((h = d.getHours() % 12) ? h : 12).zf(2);
            case "mm": return d.getMinutes().zf(2);
            case "ss": return d.getSeconds().zf(2);
            case "a/p": return d.getHours() < 12 ? "오전" : "오후";
            default: return $1;
        }
    });
};

String.prototype.string = function(len){var s = '', i = 0; while (i++ < len) { s += this; } return s;};
String.prototype.zf = function(len){return "0".string(len - this.length) + this;};
Number.prototype.zf = function(len){return this.toString().zf(len);};


function toHumanReadableTimestamp(thattime, nowtime) {
    if (typeof(thattime)==='undefined') {
        return 'just now';
    }
    let now = typeof(nowtime)!=='undefined'?nowtime:new Date().getTime();
    const diff = (now - thattime)/1000;
    const years = Math.floor(diff / (60 * 60 * 24 * 365));
    const months = Math.floor(diff / (60 * 60 * 24 * 30));
    const weeks = Math.floor(diff / (60 * 60 * 24 * 7));
    const days = Math.floor(diff / (60 * 60 * 24));
    const hours = Math.floor(diff / (60 * 60));
    const mins = Math.floor(diff / 60);
    const secs = Math.floor(diff);
    let ret = "";
    if (years>1) {
        ret = years + " years";
    } else if (years===1) {
        ret = "last year";
    } else if (months>1) {
        ret = months + " months";
    } else if (months===1) {
        ret = "last month";
    } else if (weeks>1) {
        ret = weeks + " weeks";
    } else if (weeks===1) {
        ret = "last week";
    } else if (days>1) {
        ret = days + " days";
    } else if (days===1) {
        ret = "yesterday";
    } else if (hours>1) {
        ret = hours + " hours";
    } else if (hours===1) {
        ret = "an hour ago";
    } else if (mins>1) {
        ret = mins + " minutes";
    } else if (mins===1) {
        ret = "a minute";
    } else if (secs>2) {
        ret = secs + " seconds";
    } else {
        ret = "just now";
    }
    return ret;
}