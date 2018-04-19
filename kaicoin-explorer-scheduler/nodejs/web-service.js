const r = require('rethinkdb');
const config = require("./config.js");
const { GetBlockchainInfo } = require('multichain-api/Commands/GetBlockchainInfo');
const { GetBlockchainParams } = require('multichain-api/Commands/GetBlockchainParams');
const { GetInfo } = require('multichain-api/Commands/GetInfo');
const { GetBlock } = require('multichain-api/Commands/GetBlock');
const { GetMiningInfo } = require('multichain-api/Commands/GetMiningInfo');
const { GetRawTransaction } = require('multichain-api/Commands/GetRawTransaction');


// lastBlock -> blocknotify or... get height
module.exports = function() {

    function onOrmError(e) {
        if (e) { console.error('onOrmError ' + e); }
    }

    function onOrmError(e, conn) {
        if (e) { console.error('onOrmError ' + e); }
        if (conn) { conn.close(); }
    }

    return {
        getBlocks: function() {
            self = this;
            return new Promise( function(resolve, reject) {
                r.connect(rethinkdb, function (e, conn) {
                    if (e) {
                        console.warn("" + e.message);
                        reject(e);
                        return;
                    }
                    r.table(table.TB_BLOCKS).orderBy(r.desc(table.PK_TB_BLOCKS)).limit(10).run(conn).then(function (res1) {
                        // console.log('res1 ' + JSON.stringify(res1));
                        resolve(res1);
                    }).error(function (e) {
                        onOrmError(e, conn);
                        reject(e);
                    });
                });
            });
        },
        // {"hash":"00000000553462aa2ccbeb5e338149e878184f2f4dfcca34faefe854794b5678",
        // "miner":"15NoNwNVWSDBEoJKqd5ACYoGGMayDRPi2uvQZy","confirmations":1,"size":302,"height":189746,"version":3,
        // "merkleroot":"5a781983c9b57e42074e58a6faf00e8b199cbdd2c00166ea66437db5f0f2e80b",
        // "tx":["5a781983c9b57e42074e58a6faf00e8b199cbdd2c00166ea66437db5f0f2e80b"],"time":1522170484,"nonce":26455913,
        // "bits":"1d00c2fc","difficulty":1.31290568,"chainwork":"0000000000000000000000000000000000000000000000000001c768c82fa000",
        // "previousblockhash":"000000000a2ad0760bb5e5eb9fbc7a007dbd209a551c9b8b1f55a18186f50e90"}
        getBlock: function(bhash) {
            self = this;
            rpc(GetBlock(bhash)).then(res => {
                console.log('res ' + JSON.stringify(res.result))
                self.saveItem(table.TB_BLOCKS, res.result);
                // getrawtransaction
            }).catch(e => console.log(e));
        },
        // getdifficulty getmininginfo getpeerinfo getinfo
        getSummary: function() {
            self = this;
            return new Promise( function(resolve, reject) {
                rpc(GetBlockchainInfo()).then(res1 => {
                        rpc(GetBlockchainParams()).then(res2 => {
                            rpc(GetInfo()).then(res3 => {
                                rpc(GetMiningInfo()).then(res4 => {
                                    var item = Object.assign(res1.result, res2.result, res3.result);
                                    self.saveSummary(item, res4.result);
                                    resolve(item);
                                }).catch(error => reject(error));
                            }).catch(error => reject(error));
                    }).catch(error => reject(error));
                }).catch(error => reject(error));
            });
        },
        getList: function(tablename, params) {
            console.log('item ' + JSON.stringify(params));
            r.connect(rethinkdb, function(e, conn) {
                if (e) {
                    console.warn("" + e.message);
                    return;
                }
                r.table(tablename).get(10, {index:'height'}).run(conn).then(function(res1) {
                    console.log('save ' + JSON.stringify(res1));
                    var changed = res1.inserted + res1.replaced;
                    if (changed!==1) {
                        console.error("not inserted to " + tablename);
                    } else {
                        console.log("inserted to " + tablename);
                    }
                }).error(function(e) {
                    onOrmError(e, conn);
                });
            });
        },
        getRecentTxs: function() {
            // mempool = abe.store.get_rawmempool(chain)
            // recenttx = abe.store.get_recent_transactions_as_json(chain, 10)
            // num_txs = abe.store.get_number_of_transactions(chain)
            // num_addresses = abe.store.get_number_of_addresses(chain)
            // connection_status = True
            //
            // num_peers = abe.store.get_number_of_peers(chain)
            // num_assets = abe.store.get_number_of_assets(chain)
            // num_streams = abe.store.get_number_of_streams(chain)

            // started = nTime - seconds
            // chain_age = now - started
            // since_block = now - nTime
            // listpermissions
        },
        // liststreams liststreamitems
        // IN: 'de6418206a3e1d5e8cbd79a044a618bb3788d6835a34761975081bb8a1a9bb00'
        // OUT: {"result":"01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff0d03e1ba020103062f503253482fffffffff0200f6701e160000001976a9141c3cb9d94bb987f6ef33e8ad0fa5dc4bf8310ecb88ac0000000000000000726a4c6f53504b6247304502210098ea194eca5c84e24e66e73e624d6ee7b21ba8fc26127f8ada799a353542f0d402201b43da7746c2ea676ebcdb5991d38f68baa29502f2a2ccba2ca52f324363fc43022102eee8a4eb1a6cf11df93167bca8e119f3f1937305a27cdc58810c0459438a1a4d00000000","error":null,"id":null}
        getRawTransaction: function(txhash) {
            // getrawtransaction
            rpc(GetRawTransaction(txhash, 1)).then(res1 => {
                console.log('GetRawTransaction ' + JSON.stringify(res1));
            }).catch(e => console.log(e));
        }
        /*{
            "result": {
                "hex": "01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff0d03e1ba020103062f503253482fffffffff0200f6701e160000001976a9141c3cb9d94bb987f6ef33e8ad0fa5dc4bf8310ecb88ac0000000000000000726a4c6f53504b6247304502210098ea194eca5c84e24e66e73e624d6ee7b21ba8fc26127f8ada799a353542f0d402201b43da7746c2ea676ebcdb5991d38f68baa29502f2a2ccba2ca52f324363fc43022102eee8a4eb1a6cf11df93167bca8e119f3f1937305a27cdc58810c0459438a1a4d00000000",
                "txid": "de6418206a3e1d5e8cbd79a044a618bb3788d6835a34761975081bb8a1a9bb00",
                "version": 1,
                "locktime": 0,
                "vin": [{
                    "coinbase": "03e1ba020103062f503253482f",
                    "sequence": 4294967295
                }],
                "vout": [{
                    "value": 950,
                    "n": 0,
                    "scriptPubKey": {
                        "asm": "OP_DUP OP_HASH160 1c3cb9d94bb987f6ef33e8ad0fa5dc4bf8310ecb OP_EQUALVERIFY OP_CHECKSIG",
                        "hex": "76a9141c3cb9d94bb987f6ef33e8ad0fa5dc4bf8310ecb88ac",
                        "reqSigs": 1,
                        "type": "pubkeyhash",
                        "addresses": ["14pMM8fbpk7ZdMrHjvwufPrZ29c8JAnM33gkQW"]
                    }
                }, {
                    "value": 0,
                    "n": 1,
                    "scriptPubKey": {
                        "asm": "OP_RETURN 53504b6247304502210098ea194eca5c84e24e66e73e624d6ee7b21ba8fc26127f8ada799a353542f0d402201b43da7746c2ea676ebcdb5991d38f68baa29502f2a2ccba2ca52f324363fc43022102eee8a4eb1a6cf11df93167bca8e119f3f1937305a27cdc58810c0459438a1a4d",
                        "hex": "6a4c6f53504b6247304502210098ea194eca5c84e24e66e73e624d6ee7b21ba8fc26127f8ada799a353542f0d402201b43da7746c2ea676ebcdb5991d38f68baa29502f2a2ccba2ca52f324363fc43022102eee8a4eb1a6cf11df93167bca8e119f3f1937305a27cdc58810c0459438a1a4d",
                        "type": "nulldata"
                    },
                    "data": ["53504b6247304502210098ea194eca5c84e24e66e73e624d6ee7b21ba8fc26127f8ada799a353542f0d402201b43da7746c2ea676ebcdb5991d38f68baa29502f2a2ccba2ca52f324363fc43022102eee8a4eb1a6cf11df93167bca8e119f3f1937305a27cdc58810c0459438a1a4d"]
                }],
                "blockhash": "0000000048c239a5d4fa7141f42f9e747bd5aa0cef8ffb13e96ff32118d49910",
                "confirmations": 3,
                "time": 1522927316,
                "blocktime": 1522927316
            },
            "error": null,
            "id": null
        }*/
    };

};


