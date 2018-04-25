const { RpcClient } = require('multichain-api/RpcClient');

rethinkdb = {
    host: "localhost",
    port: 28015,
    authKey: "",
    db: "crypto"
};

SERVICE_IP = '0.0.0.0';
WEB_PORT = 80;

CHAIN_NAME = 'kaicoin';
LIST_COUNT_MAIN = 8;
LIST_COUNT_PER_PAGE = 12;

// all config options are optional
rpc = RpcClient({
    protocol: 'http',
    host: '127.0.0.1',
    port: 8888,
    username: 'multichainrpc',
    password: 'Ch68iSofMDXfWwnXbJR8dGW3Mk9sy88rBycudV8eNhAq' // Company
    // password: 'Hcf5hR3GvHyo9kek4t33V3nMmjagbyKataUGmNDt5riG' // Home
    // password: '9mFcgZEZquhu86r4uALu5djnEutRjueUia9pxjkqmCti' // naver
});


table = {

    TB_SUMMARY   : "TB_SUMMARY",
    TB_BLOCKS    : "TB_BLOCKS",
    TB_TXS       : "TB_TXS",
    TB_LAST_SYNC : "TB_LAST_SYNC",

    TB_MINING    : "TB_MINING",
    TB_PRICE     : "TB_KAI_PRICE",
    TB_SYMBOLS   : "TB_SYMBOLS",

    PK_SUMMARY   : "chainname",
    PK_BLOCKS    : "height",
    PK_TXS       : "txid",
    IDX_TXS      : "time",
    PK_LAST_SYNC : "chainname",

    PK_MINING    : "chainname",
    PK_TB_PRICE  : "server_time"
};
