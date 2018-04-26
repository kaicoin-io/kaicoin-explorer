const r = require('rethinkdb');
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
        getBlocks: function(conn, count, maxheight) {
            const self = this;
            return new Promise( function(resolve, reject) {
                if (typeof(maxheight)!=='undefined') {
                    console.log('pagenated ' + maxheight);
                    r.table(table.TB_BLOCKS).orderBy({index: r.desc(table.PK_BLOCKS)}).filter(r.row(table.PK_BLOCKS)
                        .le(parseInt(maxheight, 10))).limit(count).run(conn).then(cur1 => {
                            self.handleBlocks(conn, resolve, reject, cur1, count)
                    }).error(function (e) {
                        onDBError(e, conn);
                        reject(e);
                    });
                } else {
                    r.table(table.TB_BLOCKS).orderBy({index: r.desc(table.PK_BLOCKS)}).limit(count).run(conn).then(cur1 => {
                        self.handleBlocks(conn, resolve, reject, cur1, count)
                    }).error(function (e) {
                        onDBError(e, conn);
                        reject(e);
                    });
                }
            });
        },
        handleBlocks: function(conn, resolve, reject, cur1, count) {
            cur1.toArray().then(function (list) {
                cur1.close();
                if (list.length < 1) {
                    resolve([]);
                } else {
                    const now = new Date().getTime();
                    for (let i = 0; i < list.length; i++) {
                        if (count === LIST_COUNT_MAIN) {
                            list[i].date = toHumanReadableTimestampMain(list[i].time * 1000, now);
                        } else {
                            list[i].date = toHumanReadableTimestamp(list[i].time * 1000, now);
                        }
                    }
                    resolve(list);
                }
            }).error(function (e) {
                onCursorError(e, cur1, conn);
                reject(e);
            });
        },
        /**
         * Getting Block Info
         * @param bhash | bheight
         * { hash, miner, confirmations, size, height, version, merkleroot, tx:[], time, nonce, bits, difficulty, chainwork, previousblockhash }
         */
        getBlock: function(q) {
            return new Promise( function(resolve, reject) {
                rpc(GetBlock(q)).then(res => {
                    const now = new Date().getTime();
                    let item = Object.assign(res.result, {date: toHumanReadableTimestampAgo(res.result.time*1000, now)});
                    resolve({q: q, item: item, raw: res.result });
                }).catch(e => { onRpcError(e); reject(e); });
            });
        },
        getList: function(conn, tablename, index, length, params) {
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
        getRowCount: function(conn, tablename) {
            const self = this;
            return new Promise( function(resolve, reject) {
                r.table(tablename).count().run(conn).then(count => {
                    resolve(count);
                }).error(function (e) {
                    onDBError(e, conn);
                    reject(e);
                });
            });
        },
        /**
         * get TXs from DB and from raw memory pool
         * GetRawMemPool returns: a list of transaction IDs which are in the node’s memory pool (see getmempoolinfo).
         * @param conn
         * @param count
         * @returns {Promise<any>}
         */
        getTxs: function(conn, count) {
            const self = this;
            return new Promise( function(resolve, reject) {
                self.getList(conn, table.TB_TXS, table.IDX_TXS, count).then(res1 => {
                    rpc(GetRawMemPool()).then(res2 => {
                        if (res2.error==null && res2.result.length>0) {
                            // mem pool: {"result":["11bab06911678f9eeaecf29e616ce43f5616e39bcc4fdab7306532749b2629d2",
                            //    "66db1d9c8a7203a26dbf62a957579328307e0d998deb8f2b66277c08772d5dee"],"error":null,"id":null}
                            console.warn('mem pool exists: ' + JSON.stringify(res2));
                            let rawTxArr = [];
                            self.getRawTxs(res2.result, rawTxArr).then(res3 => {
                                if (typeof(res3)!=='undefined' && res3.length>0) {
                                    for (let i=0; i<res3.length; i++) {
                                        res1.unshift(res3[i]);
                                    }
                                }
                                self.mergeTxList(res1, count, resolve);
                            });
                        } else {
                            self.mergeTxList(res1, count, resolve);
                        }
                    }).catch(e => { onRpcError(e); reject(e); });
                });
            });
        },
        mergeTxList: function(res1, count, resolve) {
            // iterate over each transaction
            const self = this;
            const now = new Date().getTime();
            for (let i=0; i<res1.length; i++) {
                self.convertRawTxToNormal(res1[i], count, now);
            }
            resolve(res1);
        },
        convertRawTxToNormal: function(item, count, now) {
            console.log('item ' + JSON.stringify(item));
            let from = '', to = '';
            if (count===LIST_COUNT_MAIN) {
                item.date = toHumanReadableTimestampMain(item.time*1000, now);
            } else {
                item.date = toHumanReadableTimestamp(item.time*1000, now);
            }
            to = item.vout[0].scriptPubKey.addresses[0];
            if (typeof(item.vin)!=='undefined' && typeof(item.vin[0].coinbase)!=='undefined') {
                item.txtype = 'mine';
            } else {
                if (typeof(item.vout)!=='undefined') {
                    from = item.vout[1].scriptPubKey.addresses[0];
                    item.from = from;
                    item.to   = to;
                    if (typeof(item.vout[1])!=='undefined') {
                        item.txtype = 'send';
                    } else {
                        item.txtype = 'comb';
                    }
                }
            }
        },
        getRawTx: function(txid) {
            return new Promise( function(resolve, reject) {
                rpc(GetRawTransaction(txid, 1)).then(res1 => {
                    // blockhash, confirmations, time, blocktime, hex, txid, version, locktime
                    let tx = {};
                    Object.assign(tx, res1.result);
                    tx.fromaddress = '';
                    tx.date = toHumanReadableTimestampAgo(tx.time*1000, new Date().getTime());
                    if (typeof(tx.vin[0].coinbase)!=='undefined') {
                        // 빈블럭이면
                        tx.txtype = 'mine';
                        tx.toaddress = tx.vout[0].scriptPubKey.addresses[0];
                        tx.value = tx.vout[0].value;
                    } else {
                        // Todo: 여기서 또 분기 필요할 듯, 송금건/다중송금건/메시지ONLY 등..
                        if (typeof(tx.vout[1])!=='undefined') {
                            tx.fromaddress = tx.vout[1].scriptPubKey.addresses[0];
                        }
                        if (tx.fromaddress.length<1) {
                            tx.txtype = 'self';
                        } else {
                            tx.txtype = 'send';
                        }
                        tx.toaddress = tx.vout[0].scriptPubKey.addresses[0];
                        tx.value = tx.vout[0].value;
                    }
                    const item = { raw: res1.result, item: tx };
                    console.log('tx ' + JSON.stringify(tx));
                    resolve(item);
                }).catch(e => { onRpcError(e); reject(e); });
            });
        },
        getRawTxs: function(txidarray, txarray) {
            const self = this;
            return new Promise( function(resolve, reject) {
                const idx = txarray.length;
                rpc(GetRawTransaction(txidarray[idx], 1)).then(res1 => {
                    // blockhash, confirmations, time, blocktime, hex, txid, version, locktime
                    let tx = { ismemp: true };
                    tx.date = toHumanReadableTimestampAgo(tx.time*1000, new Date().getTime());
                    if (typeof(tx.vin[0].coinbase)!=='undefined') {
                        // 빈블럭이면
                        tx.txtype = 'mine';
                        tx.toaddress = tx.vout[0].scriptPubKey.addresses[0];
                        tx.value = tx.vout[0].value;
                    } else {
                        // Todo: 여기서 또 분기 필요할 듯, 송금건/다중송금건/메시지ONLY 등..
                        if (typeof(tx.vout[1])!=='undefined') {
                            tx.fromaddress = tx.vout[1].scriptPubKey.addresses[0];
                        }
                        if (tx.fromaddress.length<1) {
                            tx.txtype = 'self';
                        } else {
                            tx.txtype = 'send';
                        }
                        tx.toaddress = tx.vout[0].scriptPubKey.addresses[0];
                        tx.value = tx.vout[0].value;
                    }
                    txarray.push(tx);
                    if (txarray.length<txidarray.length) {
                        self.getRawTxs(txidarray, txarray);
                    } else {
                        resolve(txarray);
                    }
                }).catch(e => { onRpcError(e); reject(e); });
            });
        }
    };
};

function toHumanReadableTimestampMain(thattime, nowtime) {
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
        ret = years + "yrs";
    } else if (years===1) {
        ret = "1yrs";
    } else if (months>1) {
        ret = months + "mons";
    } else if (months===1) {
        ret = "1mon";
    } else if (weeks>1) {
        ret = weeks + "wks";
    } else if (weeks===1) {
        ret = "1wk";
    } else if (days>1) {
        ret = days + "days";
    } else if (days===1) {
        ret = "1day";
    } else if (hours>1) {
        ret = hours + "hrs";
    } else if (hours===1) {
        ret = "1hr";
    } else if (mins>1) {
        ret = mins + "mins";
    } else if (mins===1) {
        ret = "1min";
    } else if (secs>2) {
        ret = secs + "secs";
    } else {
        ret = "now";
    }
    return ret;
}

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
        ret = "1 hour";
    } else if (mins>1) {
        ret = mins + " mins";
    } else if (mins===1) {
        ret = "1 min";
    } else if (secs>2) {
        ret = secs + " secs";
    } else {
        ret = "just now";
    }
    return ret;
}

function toHumanReadableTimestampAgo(thattime, nowtime) {
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

