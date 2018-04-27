const r = require('rethinkdb');
const util = require('./common/util')
const { GetInfo } = require('multichain-api/Commands/GetInfo');
const { GetBlockchainInfo } = require('multichain-api/Commands/GetBlockchainInfo');
const { GetBlockchainParams } = require('multichain-api/Commands/GetBlockchainParams');
const { GetMiningInfo } = require('multichain-api/Commands/GetMiningInfo');
const { ListBlocks } = require('multichain-api/Commands/ListBlocks');
const { GetBlock } = require('multichain-api/Commands/GetBlock');
const { GetRawTransaction } = require('multichain-api/Commands/GetRawTransaction');


module.exports = function() {

    function onRpcError(e) { if (e) { console.error('rpc error ' + e); } }

    function onDBError(e, conn) {
        if (e) { console.error('DB error ' + e); }
        if (conn) { conn.close(); }
    }

    return {
        syncSummary: function() {
            const self = this;
            return new Promise( function(resolve, reject) {
                rpc(GetBlockchainInfo()).then(res1 => {
                    rpc(GetBlockchainParams()).then(res2 => {
                        rpc(GetInfo()).then(res3 => {
                            rpc(GetMiningInfo()).then(res4 => {
                                // Todo: add stream info, add txcount info
                                const item = Object.assign(res1.result, res2.result, res3.result, res4.result);
                                self.savePromise(resolve, reject, table.TB_SUMMARY, item);
                            }).catch(e => reject(e));
                        }).catch(e => reject(e));
                    }).catch(e => reject(e));
                }).catch(e => reject(e));
            });
        },
        saveOnce: function(tablename, item) {
            //
            return new Promise( function(resolve, reject) {
                r.table(tablename).insert(item, { conflict: 'update', returnChanges: false })
                    .run(conn).then(function (res1) {
                    resolve(res1);
                });
            });
        },
        savePromise: function(resolve, reject, tablename, item) {
            r.table(tablename).insert(item, { conflict: 'update', returnChanges: false })
                .run(conn).then( function(res1) {
                    resolve(item);
                });
        },
        saveItem: function(conn, tablename, item) {
            return new Promise( function(resolve, reject) {
                r.table(tablename).insert(item, { conflict: 'update', returnChanges: false })
                    .run(conn).then(function (res1) {
                        resolve(res1);
                });
            });
        },
        saveList: function(conn, tablename, list) {
            return new Promise( function(resolve, reject) {
                r.table(tablename).insert(list, {
                    conflict: 'update', returnChanges: false
                }).run(conn).then(function (res1) {
                    // console.log('savelist: ' + JSON.stringify(res1));
                    resolve(res1);
                });
            });
        },
        getItem: function(conn, tablename, pk) {
            return new Promise( function(resolve, reject) {
                r.table(tablename).get(pk).run(conn).then( res1 => {
                    resolve(res1);
                }).error(function (e) {
                    onDBError(e, conn);
                    reject(e);
                });
            });
        },
        getLastBlock: function(conn) {
            const self = this;
            return new Promise( function(resolve, reject) {
                self.getItem(conn, table.TB_LAST_SYNC, CHAIN_NAME).then(res1 => {
                    console.log('[INFO] last block: ' + JSON.stringify(res1));
                    resolve(res1);
                });
            });
        },
        /**
         * sync blocks: 0-221,160
         * gap 221,160 count 73,720 mod
         * @param conn
         * @param fromHeight
         * @param toHeight
         * @returns {Promise<any>}
         */
        syncBlocks: function(conn, fromHeight, toHeight) {
            const self = this;
            return new Promise( function(resolve, reject) {
                self.listBlocks(resolve, reject, conn, fromHeight, toHeight);
            });
        },
        listBlocks: function(resolve, reject, conn, fromHeight, toHeight) {
            const self = this;
            const gap = toHeight - fromHeight;
            let localToHeight = 0;
            if (gap>ITER_COUNT_ONCE) {
                localToHeight = fromHeight + ITER_COUNT_ONCE;
            } else {
                localToHeight = fromHeight + gap;
            }
            // console.log('sync blocks: ' + fromHeight + '-' + localToHeight + ' (' + gap + ' ea)');
            rpc(ListBlocks((fromHeight+'-'+localToHeight), true)).then(res1 => {
                // console.log('listblocks ' + JSON.stringify(res1));
                if (res1.error===null) {
                    self.saveList(conn, table.TB_BLOCKS, res1.result).then(res2 => {
                        console.log('[DEBUG] blocks [' + fromHeight + '-' + localToHeight + '] ' + JSON.stringify(res2));
                        self.saveItem(conn, table.TB_LAST_SYNC, {chainname: CHAIN_NAME, blocksyncheight: localToHeight}).then(res2 => {
                            if (localToHeight>=toHeight) {
                                resolve(res1);
                            } else {
                                localToHeight++;
                                self.listBlocks(resolve, reject, conn, localToHeight, toHeight);
                            }
                        });
                    });
                }
            }).catch(e => reject(e));
        },
        getBlocksThenSaveTxs: function(conn, fromHeight, toHeight) {
            const self = this;
            return new Promise( function(resolve, reject) {
                self.getTxsFromBlock(resolve, reject, conn, fromHeight, toHeight);
            });
        },
        getTxsFromBlock: function(resolve, reject, conn, fromHeight, toHeight) {
            const self = this;
            rpc(GetBlock(''+fromHeight)).then(res1 => {
                if (res1.error===null) {
                    if (typeof(res1.result.tx)!=='undefined' && res1.result.tx.length>0) {
                        // console.log('[DEBUG] block[' + fromHeight + '] txs: ' + JSON.stringify(res1.result.tx));
                        // TX 배열 반복
                        self.getRawTx(conn, fromHeight, res1.result.tx);
                        // console.log('res2 ' + JSON.stringify(res2));
                        if (fromHeight >= toHeight) {
                            resolve();
                        } else {
                            fromHeight++;
                            self.getTxsFromBlock(resolve, reject, conn, fromHeight, toHeight);
                        }
                    } else {
                        fromHeight++;
                        self.getTxsFromBlock(resolve, reject, conn, fromHeight, toHeight);
                    }
                } else {
                    reject(res1.error);
                }
            }).catch(e => reject(e));
        },
        getRawTx: function(conn, fromHeight, txs) {
            const self = this;
            rpc(GetRawTransaction(txs[0], 1)).then(res1 => {
                self.saveItem(conn, table.TB_TXS, res1.result).then(res2 => {
                    // console.log('[DEBUG] block['+fromHeight+'] tx saving: ' + JSON.stringify(res2) + ' ' + txs[0]);
                    txs.shift();
                    if (txs.length > 0) {
                        // 배열에 남은게 있으면
                        self.getRawTx(conn, fromHeight, txs);
                    } else {
                        // 배열에 남은게 없으면
                        // Todo: 커넥션 클로즈 에러발생!!
                        self.saveItem(conn, table.TB_LAST_SYNC, {
                            chainname: CHAIN_NAME,
                            txsyncheight: fromHeight
                        }).then(res3 => {
                            if (fromHeight%200===0) {
                                console.log('[DEBUG] getting TXs in block['+fromHeight+']');
                            }
                        });
                    }
                });
            }).catch(e => {
                console.error('failed to get raw transaction ' + e);
                txs.shift();
                if (txs.length > 0) {
                    // 배열에 남은게 있으면
                    self.getRawTx(conn, fromHeight, txs);
                }
            });
        },
    };

};

// liststreams liststreamitems
// IN: 'de6418206a3e1d5e8cbd79a044a618bb3788d6835a34761975081bb8a1a9bb00'
// OUT: {"result":"01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff0d03e1ba020103062f503253482fffffffff0200f6701e160000001976a9141c3cb9d94bb987f6ef33e8ad0fa5dc4bf8310ecb88ac0000000000000000726a4c6f53504b6247304502210098ea194eca5c84e24e66e73e624d6ee7b21ba8fc26127f8ada799a353542f0d402201b43da7746c2ea676ebcdb5991d38f68baa29502f2a2ccba2ca52f324363fc43022102eee8a4eb1a6cf11df93167bca8e119f3f1937305a27cdc58810c0459438a1a4d00000000","error":null,"id":null}
// getRawTransaction: function(txhash) {
//     // getrawtransaction
//     rpc(GetRawTransaction(txhash, 1)).then(res1 => {
//         console.log('GetRawTransaction ' + JSON.stringify(res1));
//     }).catch(e => console.log(e));
// }
// GetRawTransaction
// {"result":{"hex":"01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff0d03e1ba020103062f503253482fffffffff0200f6701e160000001976a9141c3cb9d94bb987f6ef33e8ad0fa5dc4bf8310ecb88ac0000000000000000726a4c6f53504b6247304502210098ea194eca5c84e24e66e73e624d6ee7b21ba8fc26127f8ada799a353542f0d402201b43da7746c2ea676ebcdb5991d38f68baa29502f2a2ccba2ca52f324363fc43022102eee8a4eb1a6cf11df93167bca8e119f3f1937305a27cdc58810c0459438a1a4d00000000","txid":"de6418206a3e1d5e8cbd79a044a618bb3788d6835a34761975081bb8a1a9bb00","version":1,"locktime":0,"vin":[{"coinbase":"03e1ba020103062f503253482f","sequence":4294967295}],"vout":[{"value":950,"n":0,"scriptPubKey":{"asm":"OP_DUP OP_HASH160 1c3cb9d94bb987f6ef33e8ad0fa5dc4bf8310ecb OP_EQUALVERIFY OP_CHECKSIG","hex":"76a9141c3cb9d94bb987f6ef33e8ad0fa5dc4bf8310ecb88ac","reqSigs":1,"type":"pubkeyhash","addresses":["14pMM8fbpk7ZdMrHjvwufPrZ29c8JAnM33gkQW"]}},{"value":0,"n":1,"scriptPubKey":{"asm":"OP_RETURN 53504b6247304502210098ea194eca5c84e24e66e73e624d6ee7b21ba8fc26127f8ada799a353542f0d402201b43da7746c2ea676ebcdb5991d38f68baa29502f2a2ccba2ca52f324363fc43022102eee8a4eb1a6cf11df93167bca8e119f3f1937305a27cdc58810c0459438a1a4d","hex":"6a4c6f53504b6247304502210098ea194eca5c84e24e66e73e624d6ee7b21ba8fc26127f8ada799a353542f0d402201b43da7746c2ea676ebcdb5991d38f68baa29502f2a2ccba2ca52f324363fc43022102eee8a4eb1a6cf11df93167bca8e119f3f1937305a27cdc58810c0459438a1a4d","type":"nulldata"},"data":["53504b6247304502210098ea194eca5c84e24e66e73e624d6ee7b21ba8fc26127f8ada799a353542f0d402201b43da7746c2ea676ebcdb5991d38f68baa29502f2a2ccba2ca52f324363fc43022102eee8a4eb1a6cf11df93167bca8e119f3f1937305a27cdc58810c0459438a1a4d"]}],"blockhash":"0000000048c239a5d4fa7141f42f9e747bd5aa0cef8ffb13e96ff32118d49910","confirmations":116,"time":1522927316,"blocktime":1522927316},"error":null,"id":null}
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