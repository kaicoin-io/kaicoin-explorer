'use strict'

const fastify = require('fastify')();
const path = require('path');
const resolve = path.resolve;
const service = require("./nodejs/explorer-service")();
const plugin = require("./nodejs/common/fastify-plugin");
const config   = require('./nodejs/config');
const templatesFolder = 'views';
const dao = require('./nodejs/common/dao');
// const SocketIo = require('socket.io');
// const r = require('rethinkdb');
// const socketEvents = require('./nodejs/socket-handler.js');

fastify.register(require('fastify-static'), {
    root: path.join(__dirname, 'public'),
    prefix: '/res/'
});

fastify.register(plugin, {
    engine: { ejs: require('ejs') },
    includeViewExtension: true,
    templates: templatesFolder,
    options: { filename: resolve(templatesFolder) },
    charset: 'utf-8'
});

function onHTTPError(res) {
    return function(e) {
        res.send(500, {error: e.message});
    }
}

/**
 * Main - index/dashboard page
 */
fastify.get('/', (req, res) => {
    service.getMainData().then(res1 => {
        console.log('main data ' + JSON.stringify(res1));
        res.view('index', res1);
    }).catch(function(e) {
        console.log(e);
        // res.view('error', e);
        res.send(500, {error: e.message});
    });
});

/**
 * Blockchain summary
 */
fastify.get('/summary', (req, reply) => {
    service.getSummary().then(res1 => {
        reply.view('summary', {item: res1});
    }).catch(function(e) {
        res.send(500, {error: e.message});
    });
});

/**
 * Block list
 */
fastify.get('/blocks', (req, res) => {
    service.getBlocksFirst(LIST_COUNT_PER_PAGE).then(
        res1 => {
            res.view('blocks', res1);
    }).catch(function(e) {
        console.log(JSON.stringify(e));
        res.send(500, {error: e.message});
    });
});

/**
 * * Block list
 *   - for AJAX pager
 */
fastify.get('/blocks/:q', (req, res) => {
    const json = res.code(200).header('Content-Type', 'application/json');
    service.getBlocksAjax(LIST_COUNT_PER_PAGE, req.params.q).then(
        res1 => {
            json.send(res1);
    }).catch(function(e) {
        console.log(JSON.stringify(e));
        res.send(500, {error: e.message});
    });
});

/**
 * Block details
 */
fastify.get('/block/:q', (req, reply) => {
    service.getBlock(req.params.q).then(res1 => {
        console.log('item ' + JSON.stringify(res1));
        reply.view('block', res1);
    }).catch(function(e) {
        console.log(JSON.stringify(e));
        res.send(500, {error: e.message});
    });
});

/**
 * Transaction list
 *   - getmempoolinfo => BLOCKS + BLOCK + TXS + TX  ?
 */
fastify.get('/txs', (req, reply) => {
    service.getTxsFirst(LIST_COUNT_PER_PAGE).then(
        res1 => {
            reply.view('txs', res1);
    }).catch(function(e) {
        console.log(JSON.stringify(e));
        res.send(500, {error: e.message});
    });
});

/**
 * Transaction list - AJAX paging
 */
fastify.get('/txs/:q', (req, res) => {
    const json = res.code(200).header('Content-Type', 'application/json');
    service.getTxsAjax(LIST_COUNT_PER_PAGE, req.params.q).then(res1 => {
        const list = {q: req.params.q, list: res1, count: 0};
        json.send(list);
    }).catch(function(e) {
        console.log(JSON.stringify(e));
        json.send([]);
    });
});

/**
 * Transaction detail
 */
fastify.get('/tx/:q', (req, res) => {
    // 1.
    //   1) : blockhash, confirmations, time, blocktime, hex, txid, version, locktime
    //   2) vout[n].type = 'pubkeyhash'
    // 2. only mining case (empty block)
    //   1) vin[[=0?]]: coinbase, sequence
    //   2) vout[n]: n, value, scriptPubKey(asm, hex, type[=nulldata]), data[]
    //   2) vout[0]�� value, scriptPubKey.addresses[0]�� üũ�ϸ� �ɱ�..?
    // 3. send case
    //   1) vin[]: txid(..), vout[=0], scriptSig(asm, hex), sequence
    //   2) vout[n]: n, value, scriptPubKey(asm, hex, type[=pubkeyhash], reqSigs, addresses[])
    //   2) vout[0].scriptPubKey.addresses: to address
    //   2) vout[1].scriptPubKey.addresses: from address
    service.getRawTx(req.params.q).then(res1 => {
        // console.log('res1 ' + JSON.stringify(res1));
        reply.view('tx', res1);
    }).catch(function(e) {
        console.log(JSON.stringify(e));
        res.send(500, {error: e.message});
    });
});

/**
 * Address details (dev plan not fixed)
 */
fastify.get('/address/:q', (req, reply) => {
    // config.getConnection().then(conn => {
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

/**
 * Search
 * 1. if 64 chars =>
 *   1) blockhash: 000000000fcd910cf007d3c3ddcd94cc9d30b72029f1c5114b7a144f97a42cbb
 *   2) txid: a4dc6969669519d1abfd2d4f051a9f2200c981a915cedd271d300ef30e4c6f13
 *      => blockhash 00000000~~ (starts with at least 8ea of 0)
 * 2. if 38 chars and starts with '1' =>
 *   - address: e.g. 1D2WDbRBJzYHF9tRmyE2eCDixzuWJvacKZw1Pk
 * 3. if under 10 chars and only numbers =>
 *   - block height:
 */
fastify.get('/q/:q', (req, res) => {
    const param = req.params.q;
    const json = res.code(200).header('Content-Type', 'application/json');
    if (param.length>64) {
        json.send({type: null});
    } else {
        const alphanumeric = /^[0-9a-zA-Z]+$/;
        if(param.match(alphanumeric)===false) {
            json.send({type: null});
        } else {
            if (param.length===64) {
                if (param.startsWith('0000')) {
                    // block address
                    json.send({type: 'block'});
                } else {
                    // TX ID
                    json.send({type: 'tx'});
                }
            } else if (param.length===38) {
                // address
                json.send({type: 'address'});
            } else if (param.length<10) {
                //
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

/**
 * Search
 * - for backward compatibility with previous block explorer version
 */
fastify.get('/MultiChain%20kaicoin/tx/:q', (req, reply) => {
    reply.redirect('/tx/' + req.params.q);
});

/**
 * starting server
 */
fastify.listen(WEB_PORT, SERVICE_IP, err => {
    if (err) throw err;
    const io = require('socket.io')(fastify.server);
    io.origins('*:*');
    io.on('connection', function(client){
        console.log('user socket con');
        client.on('message', function(data){ console.log('message received'); });
        client.on('disconnect', function(){ console.log('user socket discon'); });
    });
    handleRealtime(io);
    console.log(`fastify server listening on ${fastify.server.address().port}`);
});

/*

io.on('connection', function (socket) {

    var addedUser = false;

    // when the client emits 'new message', this listens and executes
    socket.on('new message', function (data) {
        // we tell the client to execute 'new message'
        socket.broadcast.emit('new message', {
            username: socket.username,
            message: data
        });
    });

    // when the client emits 'add user', this listens and executes
    socket.on('add user', function (username) {
        if (addedUser) return;

        // we store the username in the socket session for this client
        socket.username = username;
        ++numUsers;
        addedUser = true;
        socket.emit('login', {
            numUsers: numUsers
        });
        // echo globally (all clients) that a person has connected
        socket.broadcast.emit('user joined', {
            username: socket.username,
            numUsers: numUsers
        });
    });

    // when the client emits 'typing', we broadcast it to others
    socket.on('typing', function () {
        socket.broadcast.emit('typing', {
            username: socket.username
        });
    });

    // when the client emits 'stop typing', we broadcast it to others
    socket.on('stop typing', function () {
        socket.broadcast.emit('stop typing', {
            username: socket.username
        });
    });

    // when the user disconnects.. perform this
    socket.on('disconnect', function () {
        if (addedUser) {
            --numUsers;

            // echo globally that this client has left
            socket.broadcast.emit('user left', {
                username: socket.username,
                numUsers: numUsers
            });
        }
    });
});
*/

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
/*    r.connect(rethinkdb, function(e, conn) {
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
    });*/
}
