const r = require('rethinkdb');
const { RpcClient } = require('multichain-api/RpcClient');

rethinkdb = {
    host: "localhost",
    port: 28015,
    authKey: "",
    db: "crypto"
};

CHAIN_NAME = 'kaicoin';
// ITER_COUNT_ONCE = 100;
ITER_COUNT_ONCE = 99;

// all config options are optional
rpc = RpcClient({
    protocol: 'http',
    host: '127.0.0.1',
    port: 8888,
    username: 'multichainrpc',
    password: 'Ch68iSofMDXfWwnXbJR8dGW3Mk9sy88rBycudV8eNhAq' // Company
    //password: 'Hcf5hR3GvHyo9kek4t33V3nMmjagbyKataUGmNDt5riG' // Home
});

table = {

    TB_SUMMARY   : "TB_SUMMARY",
    TB_BLOCKS    : "TB_BLOCKS",
    TB_TXS       : "TB_TXS",
    TB_LAST_SYNC : "TB_LAST_SYNC", // {chainname:$(chainname), blocksyncheight:$(height), txsyncheight:$(height)}

    TB_MINING    : "TB_MINING",
    TB_PRICE     : "TB_KAI_PRICE",
    TB_SYMBOLS   : "TB_SYMBOLS",

    PK_SUMMARY   : "chainname",
    PK_BLOCKS    : "height",
    PK_TXS       : "txid",
    PK_LAST_SYNC : "chainname",
    IDX_TXS      : "time",

    PK_MINING    : "chainname",
    PK_TB_PRICE  : "server_time"
};

module.exports = function() {
    /*
    r.tableCreate(table.TB_SUMMARY,   {primaryKey: table.PK_SUMMARY})
    r.tableCreate(table.TB_MINING,    {primaryKey: table.PK_MINING})
    r.tableCreate(table.TB_BLOCKS,    {primaryKey: table.PK_BLOCKS})
    r.tableCreate(table.TB_TXS,       {primaryKey: table.PK_TXS})
    r.tableCreate(table.TB_LAST_SYNC, {primaryKey: table.PK_LAST_SYNC})
    */
    return {
        connectDB: function() {
            return r.connect(rethinkdb);
        },
        disconnectDB: function(conn) {
            conn.close();
        },
        checkScheme: function(conn) {
            self = this;
            console.log('[INFO] ------- scheme checking start -------');
            return new Promise( function(resolve, reject) {
                r.dbList().run(conn).then(function(dbs) {
                    console.log('existing dbs: ' + dbs);
                    let hasDB = dbs.includes(rethinkdb.db);
                    if (hasDB===false) {
                        console.log('creating DB ' + rethinkdb.db + ': ' + hasDB);
                        r.dbCreate(rethinkdb.db).run(conn).then(function(res) {
                            self.checkSummaryTable(conn, resolve);
                        });
                    } else {
                        self.checkSummaryTable(conn, resolve);
                    }
                });
            });
        },
        checkSummaryTable: function(conn, resolve) {
            r.tableList().run(conn).then(function(tables) {
                console.log('existing tables: ' + tables);
                let hasTable = tables.includes(table.TB_SUMMARY);
                if (hasTable===false) {
                    console.log('creating table: ' + table.TB_SUMMARY);
                    r.tableCreate(table.TB_SUMMARY, {primaryKey: table.PK_SUMMARY}).run(conn).then(res => {
                        self.checkBlocksTable(conn, tables, resolve);
                    });
                } else {
                    self.checkBlocksTable(conn, tables, resolve);
                }
            });
        },
        checkBlocksTable: function(conn, tables, resolve) {
            const self = this;
            let hasTable = tables.includes(table.TB_BLOCKS);
            if (hasTable === false) {
                console.log('creating table: ' + table.TB_BLOCKS);
                r.tableCreate(table.TB_BLOCKS, {primaryKey: table.PK_BLOCKS}).run(conn).then(res => {
                    self.checkTxsTable(conn, tables, resolve);
                });
            } else {
                self.checkTxsTable(conn, tables, resolve);
            }
        },
        checkTxsTable: function(conn, tables, resolve) {
            const self = this;
            let hasTable = tables.includes(table.TB_TXS);
            if (hasTable === false) {
                console.log('creating table: ' + table.TB_TXS);
                r.tableCreate(table.TB_TXS, {primaryKey: table.PK_TXS}).run(conn).then(res1 => {
                    r.table(table.TB_TXS).indexCreate(IDX_).run(conn).then(res2 => {
                        self.checkLastSyncTable(conn, tables, resolve);
                    });
                });
            } else {
                self.checkLastSyncTable(conn, tables, resolve);
            }
        },
        checkLastSyncTable: function(conn, tables, resolve) {
            const self = this;
            let hasTable = tables.includes(table.TB_LAST_SYNC);
            if (hasTable === false) {
                console.log('creating table: ' + table.TB_LAST_SYNC);
                r.tableCreate(table.TB_LAST_SYNC, {primaryKey: table.PK_LAST_SYNC}).run(conn).then(res => {
                    resolve(res);
                });
            } else {
                resolve();
            }
        }
    }
}