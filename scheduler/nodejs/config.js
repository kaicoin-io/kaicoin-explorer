const { RpcClient } = require('multichain-api/RpcClient');

SERVICE_IP          = '0.0.0.0';
WEB_PORT            = 80;

CHAIN_NAME          = 'kaicoin';
LIST_COUNT_MAIN     = 8;
LIST_COUNT_PER_PAGE = 12;
ITER_COUNT_ONCE     = 499;

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
