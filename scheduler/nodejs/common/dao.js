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
 * @returns {{getConnection: getConnection, disConnect: disConnect, checkScheme: function(*=): Promise<any>, checkTables: checkTables, checkBlocksTable: checkBlocksTable, checkTxsTable: checkTxsTable, checkLastSyncTable: checkLastSyncTable}}
 */
module.exports = function() {

    // let conn = null;
    // function connect() {
    //     if (conn===null) { return r.connect(rethinkdb);
    //     } else { return conn; }
    // }
    // function disConnect() { if (conn!==null) { conn.close(); } }

    return {
        checkScheme: function() {
            self = this;
            console.log('[INFO] ------- scheme checking start -------');
            return new Promise( function(success, fail) {
                r.connect(rethinkdb).then(function(conn) {
                    let result = {};
                    self.checkDB(conn).then(function(res1) {
                        return self.checkTables(conn);
                    }).then(function(tables) {
                        return self.checkBlocksTable(con, tables);
                    }).then(function(tables) {
                        return self.checkTxsTable(conn, tables);
                    }).then(function(tables) {
                        self.checkLastSyncTable(conn, tables);
                        success(1);
                    });
                }).error(fail);
            });
        },
        checkDB: function(conn) {
            return new Promise( function(success, fail) {
                r.dbList().run(conn).then(function(dbs) {
                    let hasDB = dbs.includes(rethinkdb.db);
                    if (hasDB===false) {
                        console.log('[INFO] DB not exists, creating: ' + rethinkdb.db);
                        r.dbCreate(rethinkdb.db).run(conn).then(function(res1) {
                            self.checkTables(conn, success, fail);
                        }).error(fail);
                    } else { self.checkTables(conn, success, fail); }
                }).error(fail);
            });
        },
        checkTables: function(conn) {
            return new Promise(function(success, fail) {
                r.tableList().run(conn).then(function(tables) {
                    let hasTable = tables.includes(table.TB_SUMMARY);
                    if (hasTable===false) {
                        console.log('[INFO] TABLE not exists, creating: ' + table.TB_SUMMARY);
                        r.tableCreate(table.TB_SUMMARY, {primaryKey: table.PK_SUMMARY}).run(conn).then(
                            res1 => { success(tables);
                        }).error(fail);
                    } else {
                        success();
                    }
                }).error(fail);
            });
        },
        checkBlocksTable: function(conn, tables) {
            const self = this;
            let hasTable = tables.includes(table.TB_BLOCKS);
            return new Promise(function(success, fail) {
                if (hasTable===false) {
                    console.log('[INFO] TABLE not exists, creating: ' + table.TB_BLOCKS);
                    r.tableCreate(table.TB_BLOCKS, {primaryKey: table.PK_BLOCKS}).run(conn).then(
                        res => { success(tables);
                    }).error(fail);
                } else { success(tables); }
            });

        },
        checkTxsTable: function(conn, tables) {
            const self = this;
            let hasTable = tables.includes(table.TB_TXS);
            return new Promise(function(success, fail) {
                if (hasTable===false) {
                    console.log('[INFO] TABLE not exists, creating: ' + table.TB_TXS);
                    r.tableCreate(table.TB_TXS, {primaryKey: table.PK_TXS}).run(conn).then(
                        res1 => {
                            console.log('[INFO] INDEX not exists, creating: ' + table.IDX_TIME);
                            r.table(table.TB_TXS).indexCreate(table.IDX_TIME).run(conn).then(
                                res2 => {
                                    success(tables);
                                }).error(fail);
                        }).error(fail);
                } else {
                    success(tables);
                }
            });
        },
        checkLastSyncTable: function(conn, tables) {
            const self = this;
            let hasTable = tables.includes(table.TB_LAST_SYNC);
            return new Promise(function(success, fail) {
                if (hasTable === false) {
                    console.log('[INFO] TABLE not exists, creating: ' + table.TB_LAST_SYNC);
                    r.tableCreate(table.TB_LAST_SYNC, {primaryKey: table.PK_LAST_SYNC}).run(conn).then(
                        res1 => { success(res1);
                    }).error(fail);
                } else {
                    success();
                }
            });
        }
    }
};