'use strict'

const fastify  = require('fastify')();
const schedule = require('node-schedule');
const service  = require('./nodejs/schedule-service')();
const config   = require('./nodejs/config');
const dao      = require('./nodejs/common/dao')();
const r        = require('rethinkdb');
const util     = require('./nodejs/common/util');

let job_running = false;

/**
 * Runs every 20sec
 */
const job = schedule.scheduleJob('*/20 * * * * *', function(){
    syncBlocks();
});

/**
 * 1) find lastblock
 *   => { blocksyncheight: 7499, chainname: "kaicoin", txsyncheight: null }
 * 2)
 */
function syncBlocks() {
    if (job_running===false) {
        // console.log('[INFO] block sync scheduler started at ' + datestr);
        job_running = true;
        service.syncBlocks().then(function(res1) {
            job_running = false;
            const datestr = new Date().format("yyyy.MM.dd HH:mm:ss");
            console.log('[INFO] block sync scheduler finished at ' + datestr);
        }).catch(function(e) {
            job_running = false;
            const datestr = new Date().format("yyyy.MM.dd HH:mm:ss");
            console.error('[INFO] block sync scheduler error at ' + datestr + ', message ' + e);
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

/**
 * Node callback listner start
 */
fastify.listen(LISTENER_PORT, err => {
    if (err) throw err
    console.info(`[INFO] blockchain listener is running on port ${fastify.server.address().port}`);
    const now = new Date().getTime();
    dao.checkScheme().then(function(res1) {
        job_running = false;
        // trace(now, 'checkScheme');
        console.log('[INFO] scheme checking finished');
    }).catch(function(e) {
        job_running = false;
        console.error('[INFO] scheme checking finished with error ' + e);
    });
});
