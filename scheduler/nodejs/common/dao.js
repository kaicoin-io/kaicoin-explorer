const r = require('rethinkdb');

rethinkdb = {
    host: "localhost",
    port: 28015,
    authKey: "",
    db: "crypto"
};

table = {

    TB_SUMMARY    : "TB_SUMMARY",
    TB_BLOCKS     : "TB_BLOCKS",
    TB_TXS        : "TB_TXS",
    TB_LAST_SYNC  : "TB_LAST_SYNC",   // {chainname:$(chainname), blocksyncheight:$(height), txsyncheight:$(height)}
    TB_ADDR_ACTIVE: "TB_ADDR_ACTIVE", // address
    TB_ADDR_HIST  : "TB_ADDR_HIST",   // type, fromaddr, toaddr, value, time

    TB_PRICE      : "TB_KAI_PRICE",
    TB_SYMBOLS    : "TB_SYMBOLS",

    PK_SUMMARY    : "chainname",
    PK_BLOCKS     : "height",
    PK_TXS        : "txid",
    PK_LAST_SYNC  : "chainname",
    IDX_TIME       : "time",

    PK_MINING    : "chainname",
    PK_TB_PRICE  : "server_time"
};

/**
 * r.tableCreate(table.TB_SUMMARY,   {primaryKey: table.PK_SUMMARY})
 * r.tableCreate(table.TB_BLOCKS,    {primaryKey: table.PK_BLOCKS})
 * r.tableCreate(table.TB_TXS,       {primaryKey: table.PK_TXS})
 * r.tableCreate(table.TB_LAST_SYNC, {primaryKey: table.PK_LAST_SYNC})
 * @returns {{getConnection: getConnection, disConnect: disConnect, checkScheme: function(*=): Promise<any>, checkSummaryTable: checkSummaryTable, checkBlocksTable: checkBlocksTable, checkTxsTable: checkTxsTable, checkLastSyncTable: checkLastSyncTable}}
 */
module.exports = function() {

    return {
        checkScheme: function() {
            job_running = true;
            self = this;
            return new Promise( function(success, fail) {
                r.connect(rethinkdb).then(function(conn) {
                    console.log('[INFO] scheme checking started');
                    self.checkDB(conn).then(function(res1) {
                    }).then(function(tables) {
                        return self.getTables(conn);
                    }).then(function(tables) {
                        return self.checkSummaryTable(conn, tables);
                    }).then(function(tables) {
                        return self.checkBlocksTable(conn, tables);
                    }).then(function(tables) {
                        return self.checkTxsTable(conn, tables);
                    }).then(function(tables) {
                        return self.checkLastSyncTable(conn, tables);
                    }).then(function(tables) {
                        if(conn) { conn.close(); }
                        success();
                    }).catch(function(e) { if(conn) { conn.close(); fail(e); } });
                }).error(fail);
            });
        },
        checkDB: function(conn) {
            return new Promise( function(success, fail) {
                r.dbList().run(conn).then(function(dbs) {
                    let hasDB = dbs.includes(rethinkdb.db);
                    if (hasDB===false) {
                        console.log('[INFO] DB ' + rethinkdb.db +  ' creating');
                        r.dbCreate(rethinkdb.db).run(conn).then(function(res1) {
                            success();
                        }).error(fail);
                    } else {
                        console.log('[INFO] DB ' + rethinkdb.db +  ' exists');
                        success();
                    }
                }).error(fail);
            });
        },
        getTables: function(conn) {
            return new Promise(function(success, fail) {
               r.tableList().run(conn).then(function(tables) {
                   success(tables);
               }).error(fail);
            });
        },
        checkSummaryTable: function(conn, tables) {
            return new Promise(function(success, fail) {
                let hasTable = tables.includes(table.TB_SUMMARY);
                if (hasTable===false) {
                    console.log('[INFO] ' + table.TB_SUMMARY + ' creating');
                    r.tableCreate(table.TB_SUMMARY, {primaryKey: table.PK_SUMMARY}).run(conn).then(
                        res1 => { success(tables);
                    }).error(fail);
                } else {
                    console.log('[INFO] ' + table.TB_SUMMARY + ' exists');
                    success(tables);
                }
            });
        },
        checkBlocksTable: function(conn, tables) {
            const self = this;
            let hasTable = tables.includes(table.TB_BLOCKS);
            return new Promise(function(success, fail) {
                if (hasTable===false) {
                    console.log('[INFO] ' + table.TB_BLOCKS + ' creating');
                    r.tableCreate(table.TB_BLOCKS, {primaryKey: table.PK_BLOCKS}).run(conn).then(
                        res => { success(tables);
                    }).error(fail);
                } else {
                    console.log('[INFO] ' + table.TB_BLOCKS + ' exists');
                    success(tables);
                }
            });

        },
        checkTxsTable: function(conn, tables) {
            const self = this;
            let hasTable = tables.includes(table.TB_TXS);
            return new Promise(function(success, fail) {
                if (hasTable===false) {
                    console.log('[INFO] ' + table.TB_TXS + ' creating');
                    r.tableCreate(table.TB_TXS, {primaryKey: table.PK_TXS}).run(conn).then(
                        res1 => {
                            console.log('[INFO] ' + table.IDX_TIME + ' creating: ');
                            r.table(table.TB_TXS).indexCreate(table.IDX_TIME).run(conn).then(
                                res2 => {
                                    success(tables);
                                }).error(fail);
                        }).error(fail);
                } else {
                    console.log('[INFO] ' + table.TB_TXS + ' exists');
                    success(tables);
                }
            });
        },
        checkLastSyncTable: function(conn, tables) {
            const self = this;
            let hasTable = tables.includes(table.TB_LAST_SYNC);
            return new Promise(function(success, fail) {
                if (hasTable === false) {
                    console.log('[INFO] ' + table.TB_LAST_SYNC + ' creating');
                    r.tableCreate(table.TB_LAST_SYNC, {primaryKey: table.PK_LAST_SYNC}).run(conn).then(
                        res1 => { success(res1);
                    }).error(fail);
                } else {
                    console.log('[INFO] ' + table.TB_LAST_SYNC + ' exists');
                    success();
                }
            });
        },
        saveOnce: function(tablename, item) {
            return new Promise( function(success, fail) {
                r.connect(rethinkdb).then(function(conn) {
                    r.table(tablename).insert(item, {conflict: 'update', returnChanges: false})
                        .run(conn).then(function (res1) {
                        conn.close();
                        success(res1);
                    });
                }).error(fail);
            });
        },
        saveListOnce: function(tablename, list) {
            return new Promise( function(success, fail) {
                r.connect(rethinkdb).then(function(conn) {
                    r.table(tablename).insert(list, {
                        conflict: 'update', returnChanges: false
                    }).run(conn).then(function (res1) {
                        // console.log('savelist: ' + JSON.stringify(res1));
                        success(res1);
                    }).error(fail);
                });
            });
        },
        getOnce: function(tablename, pk) {
            return new Promise( function(success, fail) {
                r.connect(rethinkdb).then(function(conn) {
                    r.table(tablename).get(pk).run(conn).then(function(res1) {
                        conn.close();
                        success(res1);
                    }).error(fail);
                });
            });
        },
        saveContinueItem: function(conn, tablename, item) {
            return new Promise( function(success, fail) {
                r.table(tablename).insert(item, { conflict: 'update', returnChanges: false })
                    .run(conn).then(function (res1) {
                    success(res1);
                });
            });
        },
        saveList: function(conn, tablename, list) {
            return new Promise( function(success, fail) {
                r.table(tablename).insert(list, {
                    conflict: 'update', returnChanges: false
                }).run(conn).then(function (res1) {
                    // console.log('savelist: ' + JSON.stringify(res1));
                    success(res1);
                }).error(fail);
            });
        },
        getItem: function(conn, tablename, pk) {
            return new Promise( function(success, fail) {
                r.table(tablename).get(pk).run(conn).then( res1 => {
                    success(res1);
                }).error(function (e) {
                    onDBError(e, conn);
                    fail(e);
                });
            });
        },
    }
};