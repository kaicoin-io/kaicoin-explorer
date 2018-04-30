const r = require('rethinkdb');
const dao = require('./common/dao');
const util = require('./common/util');
const { GetBlock } = require('multichain-api/Commands/GetBlock');
const { GetRawMemPool } = require('multichain-api/Commands/GetRawMemPool');
const { GetRawTransaction } = require('multichain-api/Commands/GetRawTransaction');

rethinkdb = {
    host: "localhost",
    port: 28015,
    authKey: "",
    db: "crypto"
};

module.exports = function() {

    let mempool = [];
    function onRpcError(e) { if (e) { console.error('rpc error ' + e); } }
    function onDBError(conn) {
        if (e) console.error('DB error ' + e);
        if (conn) conn.close();
    }

    return {
        /**
         * for main page
         * @returns {Promise<any>}
         */
        getMainData: function() {
            const self = this;
            return new Promise(function (success, fail) {
                let result = {};
                self.getSummary().then(function(res1) {
                    Object.assign(result, {summary: res1});
                    return self.getBlocksMain(LIST_COUNT_MAIN);
                }).then(function(res2) {
                    Object.assign(result, {blocks: res2});
                    return self.getTxsMain(LIST_COUNT_MAIN);
                }).then(function(res3) {
                    Object.assign(result, {txs: res3});
                    return dao.getRowCount(table.TB_TXS);
                }).then(function(res4) {
                    console.log('tx count ' + res4);
                    Object.assign(result, {txcount: res4});
                    success(result);
                });
            });
        },
        /**
         * for summary page
         * @returns {Promise<any>}
         */
        getSummary: function() {
            const self = this;
            return new Promise(function (success, fail) {
                r.connect(rethinkdb).then(function(conn) {
                    r.table(table.TB_SUMMARY).get(CHAIN_NAME).run(conn).then(function(res1) {
                        dao.getRowCountConnected(conn, table.TB_TXS).then(function(res2) {
                            conn.close();
                            let date = new Date();
                            date.setTime(res1["genesis-timestamp"]*1000);
                            res1["genesis-datetime"] = date.format("yyyy.MM.dd HH:mm:ss");
                            res1["txcount"] = res2;
                            console.log('summary ' + JSON.stringify(res1));
                            success(res1);
                        }).catch(fail);
                    }).error(fail);
                }).error(fail);
            });
        },
        getBlocksMain: function(count) {
            const self = this;
            return new Promise( function(success, fail) {
                r.connect(rethinkdb).then(function (conn) {
                    r.table(table.TB_BLOCKS).orderBy({index: r.desc(table.PK_BLOCKS)}).limit(count)
                        .run(conn).then(function(cur1) {
                        cur1.toArray().then(function (list) {
                            conn.close();
                            self.handleBlocks(list, count);
                            console.log('blocks ' + JSON.stringify(list));
                            success(list);
                        }).error(fail);
                    }).error(fail);
                });
            });
        },
        getBlocksFirst: function(count) {
            const self = this;
            return new Promise( function(success, fail) {
                r.connect(rethinkdb).then(function (conn) {
                    r.table(table.TB_SUMMARY).get(CHAIN_NAME).run(conn).then(function(res1) {
                        let date = new Date();
                        date.setTime(res1["genesis-timestamp"]*1000);
                        res1["genesis-datetime"] = date.format("yyyy.MM.dd HH:mm:ss");
                        r.table(table.TB_BLOCKS).orderBy({index: r.desc(table.PK_BLOCKS)}).limit(count)
                            .run(conn).then(function(cur1) {
                            cur1.toArray().then(function (list) {
                                conn.close();
                                self.handleBlocks(list, count);
                                console.log('blocks ' + JSON.stringify(list));
                                success({summary: res1, list: list});
                            }).error(fail);
                        }).error(fail);
                    }).error(fail);
                });
            });
        },
        getBlocksAjax: function(count, q) {
            const self = this;
            return new Promise( function(success, fail) {
                r.connect(rethinkdb).then(function (conn) {
                    let qint = q==='0'?(count-1):parseInt(q, 10);
                    console.log('pagenated ' + qint);
                    r.table(table.TB_BLOCKS).orderBy({index: r.desc(table.PK_BLOCKS)})
                        .filter(r.row(table.PK_BLOCKS).le(qint)).limit(count).run(conn)
                        .then(function(cur1) {
                            cur1.toArray().then(function (list) {
                                conn.close();
                                self.handleBlocks(list, count);
                                success({q: q, list: list});
                            }).error(console.log);
                        }).error(fail);
                });
            });
        },
        handleBlocks: function(list, count) {
            if (list&&list.length>0) {
                const now = new Date().getTime();
                for (let i = 0; i < list.length; i++) {
                    if (count === LIST_COUNT_MAIN) {
                        list[i].date = toHumanReadableTimestampMain(list[i].time * 1000, now);
                    } else {
                        list[i].date = toHumanReadableTimestamp(list[i].time * 1000, now);
                    }
                }
            }
        },
        /**
         * Getting Block Info
         * @param bhash | bheight
         * { hash, miner, confirmations, size, height, version, merkleroot, tx:[], time, nonce, bits, difficulty, chainwork, previousblockhash }
         */
        getBlock: function(q) {
            return new Promise( function(success, fail) {
                rpc(GetBlock(q)).then(res => {
                    const now = new Date().getTime();
                    let item = Object.assign(res.result,
                        {date: toHumanReadableTimestampAgo(res.result.time*1000, now)});
                    success({q: q, item: item, raw: res.result });
                }).catch(fail);
            });
        },
        getTxsMain: function(count) {
            const self = this;
            return new Promise( function(success, fail) {
                r.connect(rethinkdb).then(function (conn) {
                    r.table(table.TB_TXS).orderBy({index: r.desc(table.IDX_TIME)})
                        .limit(count).run(conn).then(cur1 => {
                        cur1.toArray().then(function(list) {
                            conn.close();
                            self.convertRawTxs(list, count);
                            console.log('txs ' + JSON.stringify(list));
                            success(list);
                        }).error(console.log);
                    }).error(fail);
                });
            });
        },
        getTxsFirst: function(count) {
            const self = this;
            return new Promise( function(success, fail) {
                r.connect(rethinkdb).then(function (conn) {
                    dao.getRowCountConnected(conn, table.TB_TXS).then(function(res1) {
                        r.table(table.TB_TXS).orderBy({index: r.desc(table.IDX_TIME)})
                            .limit(count).run(conn).then(cur1 => {
                            cur1.toArray().then(function(list) {
                                conn.close();
                                self.convertRawTxs(list, count);
                                for (let i=0; i<list.length; i++) {
                                    list[i].seq = res1-i;
                                }
                                console.log('txs ' + JSON.stringify(list));
                                success({count: res1, list: list});
                            }).error(fail);
                        }).error(fail);
                    }).catch(fail);
                });
            });
        },
        /**
         * get TXs from DB and from raw memory pool
         * GetRawMemPool returns: a list of transaction IDs which are in the node’s memory pool (see getmempoolinfo).
         * e.g. mem pool: {"result":["11bab06911678f9eeaecf29e616ce43f5616e39bcc4fdab7306532749b2629d2",
                           "66db1d9c8a7203a26dbf62a957579328307e0d998deb8f2b66277c08772d5dee"],"error":null,"id":null}
         * @param conn
         * @param count
         * @returns {Promise<any>}
         */
        getTxsAjax: function(count, q) {
            const self = this;
            return new Promise( function(success, fail) {
                let qint = q==='0'?count:parseInt(q, 10);
                const s = qint-count<0?0:qint-count;
                console.log('pagenated ' + s + '~' + qint);
                r.connect(rethinkdb).then(function (conn) {
                    r.table(table.TB_TXS).orderBy({index: r.asc(table.IDX_TIME)})
                        .slice(s, qint).run(conn).then(cur1 => {
                        cur1.toArray().then(function(list) {
                            conn.close();
                            self.convertRawTxs(list, count);
                            for (let i=0; i<list.length; i++) {
                                list[i].seq = s+i;
                            }
                            success(list.reverse());
                        }).error(fail);
                    }).error(fail);
                });
            });
        },
        /**
         * iterate over each transaction
         * @param list
         * @param count
         */
        convertRawTxs: function(list, count) {
            const self = this;
            const now = new Date().getTime();
            for (let i=0; i<list.length; i++) {
                delete list[i]['hex'];
                self.convertRawTx(list[i], now, count);
            }
        },
        /**
         *
         * @param item
         * @param count
         * @param now
         * @returns TYPE TXID FROM TO AMOUNT CONFIRM TIME
         */
        convertRawTx: function(item, now, count) {
            item.from = '';
            if (count===LIST_COUNT_MAIN) {
                item.date = toHumanReadableTimestampMain(item.time*1000, now);
            } else {
                item.date = toHumanReadableTimestamp(item.time*1000, now);
            }
            if (typeof(item.vin)!=='undefined' && typeof(item.vin[0].coinbase)!=='undefined') {
                item.txtype = 'mine';
            } else {
                if (typeof(item.vout)!=='undefined') {
                    if (typeof(item.vout[1])!=='undefined') { item.txtype = 'send';
                    } else { item.txtype = 'comb'; }
                }
            }
            if (typeof(item.vout)!=='undefined') {
                item.to = item.vout[0].scriptPubKey.addresses[0];
                item.amount = Number(item.vout[0].value).toLocaleString();
                if (typeof(item.vout[1]) !== 'undefined'
                    && typeof(item.vout[1].scriptPubKey.addresses) !== 'undefined') {
                    item.from = item.vout[1].scriptPubKey.addresses[0];
                }
            }
            delete item['hex'];
            delete item['data'];
            delete item['vin'];
            delete item['vout'];
        },
        /**
         * blockhash, confirmations, time, blocktime, hex, txid, version, locktime
         * @param txid
         * @returns {Promise<any>}
         */
        getRawTx: function(txid) {
            const self = this;
            return new Promise( function(success, fail) {
                rpc(GetRawTransaction(txid, 1)).then(res1 => {
                    let raw = {};
                    Object.assign(raw, res1.result);
                    self.convertRawTx(res1.result, new Date().getTime());
                    success({ raw: raw, item: res1.result });
                }).catch(e => { onRpcError(e); fail(e); });
            });
        },
        getRawTxs: function(txidarray, txarray) {
            const self = this;
            return new Promise( function(success, fail) {
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
                        success(txarray);
                    }
                }).catch(e => { onRpcError(e); fail(e); });
            });
        }
    }
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
        ret = years + "y";
    } else if (years===1) {
        ret = "1y";
    } else if (months>1) {
        ret = months + "mo";
    } else if (months===1) {
        ret = "1mo";
    } else if (weeks>1) {
        ret = weeks + "w";
    } else if (weeks===1) {
        ret = "1w";
    } else if (days>1) {
        ret = days + "d";
    } else if (days===1) {
        ret = "1d";
    } else if (hours>1) {
        ret = hours + "h";
    } else if (hours===1) {
        ret = "1h";
    } else if (mins>1) {
        ret = mins + "m";
    } else if (mins===1) {
        ret = "1m";
    } else if (secs>2) {
        ret = secs + "s";
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

/*
                rpc(GetRawMemPool()).then(res2 => {
                        if (res2.error==null && res2.result.length>0) {
                            let rawTxArr = [];
                            self.getRawTxs(res2.result, rawTxArr).then(res3 => {
                                if (typeof(res3)!=='undefined' && res3.length>0) {
                                    for (let i=0; i<res3.length; i++) {
                                        console.warn('mem pool ['+i+']: ' + JSON.stringify(res3[i]));
                                        res1.unshift(res3[i]);
                                    }
                                }
                                self.convertRawTxs(res1, count, success);
                                console.log('mem merged txs ' + JSON.stringify(res1));
                            });
                        } else {
                            self.convertRawTxs(res1, count, success);
                            console.log('txs ' + JSON.stringify(res1));
                        }
                    }).catch(e => { onRpcError(e); fail(e); });
                */

