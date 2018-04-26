'use strict'

const fastify  = require('fastify')();
const schedule = require('node-schedule');
const service  = require('./nodejs/schedule-service')();
const config   = require('./nodejs/config')();

let job_running = false;

// Runs every 2min
const job = schedule.scheduleJob('*/1 * * * *', function(){
    syncBlocks();
});

/**
 * 1) find lastblock
 *   => { blocksyncheight: 7499, chainname: "kaicoin", txsyncheight: null }
 *
 */
function syncBlocks() {
    const now = new Date();
    const starttime = now.getTime();
    const min = now.getMinutes();
    if (job_running===false) {
        job_running = true;
        console.log('--- scheduler is started at ' + min + ' min ---');
        config.connectDB().then(conn => {
            service.syncSummary(conn).then(res1 => {
                service.getLastBlock(conn).then(res2 => {
                    let fromBlock = 0;
                    let toBlock = res1.blocks;
                    if (res2!==null && typeof(res2.blocksyncheight)!=='undefined') {
                        fromBlock = res2.blocksyncheight;
                    }
                    if (toBlock>fromBlock) {
                        service.syncBlocks(conn, fromBlock+1, toBlock).then(res3 => {
                            if (typeof(res2.txsyncheight)==='undefined'
                                        || res2.txsyncheight<res2.blocksyncheight) {
                                console.log('[INFO] synching TXs');
                                const fromheight = typeof(res2.txsyncheight)==='undefined'?0:res2.txsyncheight;
                                service.getBlocksThenSaveTxs(conn, fromheight, res2.blocksyncheight).then(res4 => {
                                    console.log('[INFO] synching TXs finished');
                                    config.disconnectDB(conn);
                                    trace(starttime);
                                    job_running = false;
                                }, function (e) {
                                    console.error('[FAIL] sync TXs ' + e);
                                    config.disconnectDB(conn);
                                    trace(starttime);
                                    job_running = false;
                                });
                            } else {
                                config.disconnectDB(conn);
                                trace(starttime);
                                job_running = false;
                            }
                        });
                    } else {
                        console.log('[INFO] all blocks and TXs synched');
                        config.disconnectDB(conn);
                        trace(starttime);
                        job_running = false;
                    }
                });
            }, function (e) {
                console.error('failed to connect to blockchain ' + e);
                config.disconnectDB(conn);
                trace(starttime);
                job_running = false;
            });
        }, function (e) {
            console.error('failed to connect to DB ' + e);
            config.disconnectDB(conn);
            trace(starttime);
            job_running = false;
        });
    }
}

/**
 *
 */
fastify.get('/api/blocknotify/:bhash', (req, reply) => {
    // console.log('[INFO] new block');
    syncBlocks();
    reply.send({code:999, message:'ok'})
});

/**
 * what to do?
 */
fastify.get('/api/walletnotify/:tid', (req, reply) => {
    console.log('[INFO] new transaction ' + req.params.tid);
    reply.send({code:999, message:'ok'})
});

fastify.listen(9000, err => {
    if (err) throw err
    console.info(`[INFO] scheduler web app is listening on port ${fastify.server.address().port}`);
    config.connectDB().then(conn => {
        config.checkScheme(conn).then(res => {
            console.log('[INFO] ------- scheme checking finish -------');
            config.disconnectDB(conn);
        });
    });
});

function trace(starttime) {
    const interval = new Date().getTime() - starttime;
    console.log('[INFO] scheduler run for ' + (interval/1000) + " sec");
}
