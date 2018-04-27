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

_rdbConn = null;

/**
 * r.tableCreate(table.TB_SUMMARY,   {primaryKey: table.PK_SUMMARY})
 * r.tableCreate(table.TB_BLOCKS,    {primaryKey: table.PK_BLOCKS})
 * r.tableCreate(table.TB_TXS,       {primaryKey: table.PK_TXS})
 * r.tableCreate(table.TB_LAST_SYNC, {primaryKey: table.PK_LAST_SYNC})
 * @returns {{getConnection: getConnection, disConnect: disConnect, checkScheme: function(*=): Promise<any>, checkTables: checkTables, checkBlocksTable: checkBlocksTable, checkTxsTable: checkTxsTable, checkLastSyncTable: checkLastSyncTable}}
 */
module.exports.connect = function(req, res) {

};

module.exports.disConnect = function() {
    if (_rdbConn!==null) { _rdbConn.close(); }
};

module.exports.get = function() {

};

module.exports.getList = function() {
};

function onDBError(res) {
    return function(error) {
        res.send(500, {error: error.message});
    }
}