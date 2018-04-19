const r = require('rethinkdb');
const config = require('./config');
const { GetBlock } = require('multichain-api/Commands/GetBlock');
const { GetRawMemPool } = require('multichain-api/Commands/GetRawMemPool');
const { GetRawTransaction } = require('multichain-api/Commands/GetRawTransaction');

module.exports = function() {

    function onRpcError(e) {
        if (e) { console.error('onRpcError ' + e); }
    }

    function onDBError(e, conn) {
        if (e) { console.error('onDBError ' + e); }
        if (conn) { conn.close(); }
    }

    function onCursorError(e, cur, conn) {
        if (e) { console.error('onCursorError ' + e); }
        if (cur) { cur.close(); }
        if (conn) { conn.close(); }
    }

    return {
        // getdifficulty getmininginfo getpeerinfo getinfo
        connectDB: function() {
            return r.connect(rethinkdb);
        },
        disconnectDB: function(conn) {
            conn.close();
        },
        getSummary: function(conn) {
            // console.log('getSummary');
            return new Promise( function(resolve, reject) {
                r.table(table.TB_SUMMARY).get(CHAIN_NAME).run(conn).then( res1 => {
                    resolve(res1);
                }).error(function (e) {
                    onDBError(e, conn);
                    reject(e);
                });
            });
        },
        getBlocks: function(conn, count) {
            return new Promise( function(resolve, reject) {
                r.table(table.TB_BLOCKS).orderBy({index: r.desc(table.PK_BLOCKS)}).limit(count).run(conn).then(cur1 => {
                    cur1.toArray().then(function(list) {
                        cur1.close();
                        if (list.length<1) {
                            resolve([]);
                        } else {
                            const now = new Date().getTime();
                            for (let i=0; i<list.length; i++) {
                                list[i].date = toHumanReadableTimestamp(list[i].time*1000, now);
                            }
                            resolve(list);
                        }
                    }).error(function (e){
                        onCursorError(e, cur1, conn);
                        reject(e);
                    });
                }).error(function (e) {
                    onDBError(e, conn);
                    reject(e);
                });
            });
        },
        // { hash, miner, confirmations, size, height, version, merkleroot, tx:[]
        //   time, nonce, bits, difficulty, chainwork, previousblockhash }
        /**
         * Getting Block Info
         * @param bhash | bheight
         */
        getBlock: function(bhash) {
            self = this;
            return new Promise( function(resolve, reject) {
                rpc(GetBlock(bhash)).then(res => {
                    resolve(res.result);
                }).catch(e => { onRpcError(e); reject(e); });
            });
        },
        getList: function(conn, tablename, index, length, params) {
            // console.log('table ' + tablename + ' order by ' + index + ' desc limit ' + length);
            return new Promise( function(resolve, reject) {
                r.table(tablename).orderBy({index: r.desc(index)}).limit(length).run(conn).then(cur1 => {
                    cur1.toArray().then(function (list) {
                        cur1.close();
                        if (list.length < 1) {
                            resolve([]);
                        } else {
                            resolve(list);
                        }
                    }).error(function (e){
                        onCursorError(e, cur1, conn);
                        reject(e);
                    });
                }).error(function (e) {
                    onDBError(e, conn);
                    reject(e);
                });
            });
        },
        getTxs: function(conn, count) {
            const self = this;
            return new Promise( function(resolve, reject) {
                self.getList(conn, table.TB_TXS, table.IDX_TXS, count).then(res1 => {
                    rpc(GetRawMemPool()).then(res2 => {
                        if (res2.error==null && res2.result.length>0) {
                            // Returns a list of transaction IDs which are in the node’s memory pool (see getmempoolinfo).
                            // mem pool: {"result":["11bab06911678f9eeaecf29e616ce43f5616e39bcc4fdab7306532749b2629d2",
                            // // "66db1d9c8a7203a26dbf62a957579328307e0d998deb8f2b66277c08772d5dee"],"error":null,"id":null}
                            console.warn('mem pool exists: ' + JSON.stringify(res2));
                            for (let i=0; i<res2.result.length; i++) {
                                res1.push({txid: res2.result[i]});
                            }
                        }
                        const now = new Date().getTime();
                        for (let i=0; i<res1.length; i++) {
                            res1[i].date = toHumanReadableTimestamp(res1[i].time*1000, now);
                            if (typeof(res1[i].vin[0].coinbase)!=='undefined') {
                                res1[i].txtype = 'mine';
                            } else if (typeof(res1[i].vin)!=='undefined') {
                                // Todo: 여기서 또 분기 필요할 듯, 송금건/다중송금건/메시지ONLY 등..
                                res1[i].txtype = 'send';
                            } else {
                                res1[i].txtype = 'memp';
                            }
                        }
                        resolve(res1);
                    }).catch(e => { onRpcError(e); reject(e); });
                });
            });
        },
        getRawTx: function(txid) {
            const self = this;
            return new Promise( function(resolve, reject) {
                rpc(GetRawTransaction(txid, 1)).then(res1 => {
                    if (res1.error===null) {
                        resolve(res1.result);
                    } else {
                        resolve([]);
                    }
                }).catch(e => { onRpcError(e); reject(e); });
            });
        }
    };
};

function toHumanReadableTimestamp(thattime, nowtime) {
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
        ret = years + " years ago";
    } else if (years===1) {
        ret = "last year";
    } else if (months>1) {
        ret = months + " months ago";
    } else if (months===1) {
        ret = "last month";
    } else if (weeks>1) {
        ret = weeks + " weeks ago";
    } else if (weeks===1) {
        ret = "last week";
    } else if (days>1) {
        ret = days + " days ago";
    } else if (days===1) {
        ret = "yesterday";
    } else if (hours>1) {
        ret = hours + " hours ago";
    } else if (hours===1) {
        ret = "an hour ago";
    } else if (mins>1) {
        ret = mins + " minutes ago";
    } else if (mins===1) {
        ret = "a minute ago";
    } else if (secs>2) {
        ret = secs + " seconds ago";
    } else {
        ret = "just now";
    }
    return ret;
}
