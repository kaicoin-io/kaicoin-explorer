const r     = require('rethinkdb');
const util  = require('./common/util');
const dao   = require('./common/dao')();
const { GetInfo }               = require('multichain-api/Commands/GetInfo');
const { GetBlock }              = require('multichain-api/Commands/GetBlock');
const { ListBlocks }            = require('multichain-api/Commands/ListBlocks');
const { GetMiningInfo }         = require('multichain-api/Commands/GetMiningInfo');
const { GetRawTransaction }     = require('multichain-api/Commands/GetRawTransaction');
const { GetBlockchainInfo }     = require('multichain-api/Commands/GetBlockchainInfo');
const { GetBlockchainParams }   = require('multichain-api/Commands/GetBlockchainParams');


module.exports = function() {

    return {
        syncBlocks: function() {
            const self = this;
            return new Promise(function(success, fail) {
                let summary = {};
                let lastblock = {};
                // console.log('syncBlocks');
                self.getSummary().then(function(res1) {
                    summary = res1;
                    // console.log('getSummary ' + JSON.stringify(res1));
                    return dao.saveOnce(table.TB_SUMMARY, res1);
                }).then(function(res2) {
                    // console.log('saveSummary');
                    return self.getLastBlock();
                }).then(function(res3) {
                    console.log('[INFO] last sync block ' + JSON.stringify(res3));
                    lastblock = res3;
                    let fromBlock = 0;
                    let toBlock = summary.blocks;
                    // console.log('[INFO] toBlock ' + toBlock);
                    if (res3 !== null && typeof(res3.blocksyncheight) !== 'undefined') {
                        fromBlock = res3.blocksyncheight;
                    }
                    if (toBlock > fromBlock) {
                        // Block Sync
                        console.log('[INFO] synching blocks ' + (fromBlock+1) + '~' + toBlock);
                        return self.syncBlocksRange(fromBlock+1, toBlock);
                    } else {
                        success();
                    }
                }).then(function(res4) {
                    if (typeof(lastblock.txsyncheight) === 'undefined'
                        || lastblock.txsyncheight < lastblock.blocksyncheight) {
                        // TX Sync
                        const fromheight = typeof(lastblock.txsyncheight)==='undefined'?0:lastblock.txsyncheight;
                        if (fromheight===lastblock.blocksyncheight) { success(); }
                        return self.getTxsFromBlocks(fromheight, lastblock.blocksyncheight);
                    } else {
                        success();
                    }
                }).then(function(res5) {
                    success();
                }).catch(fail);
            });
        },
        getSummary: function() {
            const self = this;
            return new Promise(function(success, fail) {
                rpc(GetBlockchainInfo()).then(res1 => {
                    rpc(GetBlockchainParams()).then(res2 => {
                        rpc(GetInfo()).then(res3 => {
                            rpc(GetMiningInfo()).then(res4 => {
                                // Todo: add stream info, add txcount info
                                success(Object.assign(res1.result, res2.result, res3.result, res4.result));
                            }).catch(fail);
                        }).catch(fail);
                    }).catch(fail);
                }).catch(fail);
            });
        },
        getLastBlock: function() {
            const self = this;
            return new Promise( function(success, fail) {
                dao.getOnce(table.TB_LAST_SYNC, CHAIN_NAME).then(function(res1) {
                    success(res1);
                }).catch(fail);
            });
        },
        /**
         * sync blocks: 0-221,160
         * gap 221,160 count 73,720 mod
         * @param conn
         * @param fromHeight
         * @param toHeight
         * @returns {Promise<any>}
         */
        syncBlocksRange: function(fromHeight, toHeight) {
            const self = this;
            return new Promise( function(success, fail) {
                self.listBlocks(success, fail, fromHeight, toHeight);
            });
        },
        listBlocks: function(success, fail, fromHeight, toHeight) {
            // console.log('listBlocks ' + fromHeight + '~' + toHeight);
            const self = this;
            const gap = toHeight - fromHeight;
            let localToHeight = 0;
            if (gap>ITER_COUNT_ONCE) {
                localToHeight = fromHeight + ITER_COUNT_ONCE;
            } else {
                localToHeight = fromHeight + gap;
            }
            // console.log('[DEBUG] list blocks: ' + fromHeight + '-' + localToHeight + ' (' + gap + ' ea)');
            rpc(ListBlocks((fromHeight+'-'+localToHeight), true)).then(res1 => {
                // console.log('listblocks ' + JSON.stringify(res1));
                if (res1.error===null) {
                    dao.saveListOnce(table.TB_BLOCKS, res1.result).then(function(res2) {
                        console.log('[DEBUG] blocks [' + fromHeight + '-' + localToHeight + '] ' + JSON.stringify(res2));
                        dao.saveOnce(table.TB_LAST_SYNC, {chainname: CHAIN_NAME, blocksyncheight: localToHeight}).then(
                            function(res2) {
                            if (localToHeight>=toHeight) {
                                success(res1);
                            } else {
                                localToHeight++;
                                self.listBlocks(success, fail, localToHeight, toHeight);
                            }
                        }).catch(function(e) { fail (e); });
                    }).catch(function(e) { fail (e); });
                } else { fail (res1.error); }
            }).catch(e => fail(e));
        },
        getTxsFromBlocks: function(fromHeight, toHeight) {
            const self = this;
            console.log('[INFO] synching TXs started');
            return new Promise( function(success, fail) {
                self.getBlock(success, fail, fromHeight, toHeight);
            });
        },
        /**
         * 블록 재귀호출
         * @param success
         * @param fail
         * @param fromHeight
         * @param toHeight
         */
        getBlock: function(success, fail, fromHeight, toHeight) {
            const self = this;
            rpc(GetBlock('' + fromHeight)).then(function(res1) {
                if (res1.error===null) {
                    // 선별적 로그 출력
                    if (fromHeight%100===0) {
                        console.log('[DEBUG] sync TXs from block ' + fromHeight + '-> txids ' + JSON.stringify(res1.result.tx));
                    }
                    if (typeof(res1.result.tx)!=='undefined' && res1.result.tx.length>0) {
                        // TX 배열 반복
                        self.syncTxs(fromHeight, res1.result.tx).then(function(blockheight) {
                            // 배열에 남은게 없으면 마지막 TX sync 인덱스 저장
                            dao.saveOnce(table.TB_LAST_SYNC, {chainname: CHAIN_NAME, txsyncheight: blockheight})
                                .then(function (res3) {
                                    if (fromHeight >= toHeight) {
                                        // 블럭 TX 체크 완료
                                        console.log('[INFO] synching TXs finished');
                                        success(blockheight);
                                    } else {
                                        fromHeight++;
                                        self.getBlock(success, fail, fromHeight, toHeight);
                                    }
                                }).catch(fail);
                        }).catch(fail);
                    } else {
                        // TX 배열이 비었으면, 다음 블럭으로 이동
                        dao.saveOnce(table.TB_LAST_SYNC, {chainname: CHAIN_NAME, txsyncheight: blockheight})
                            .then(function (res3) {
                                if (fromHeight >= toHeight) {
                                    // 블럭 TX 체크 완료
                                    success(blockheight);
                                } else {
                                    fromHeight++;
                                    self.getBlock(success, fail, fromHeight, toHeight);
                                }
                            }).catch(fail);
                    }
                } else { fail(res1.error); }
            }).catch(fail);
        },
        syncTxs: function(fromHeight, txs) {
            const self = this;
            return new Promise(function(success, fail) {
                self.syncTx(success, fail, fromHeight, txs);
            });
        },
        syncTx: function(success, fail, fromHeight, txs) {
            const self = this;
            rpc(GetRawTransaction(txs[0], 1)).then(function (res1) {
                // console.log('[DEBUG] saving raw tx ' + JSON.stringify(res1.result));
                dao.saveOnce(table.TB_TXS, res1.result).then(function (res2) {
                    txs.shift();
                    if (txs.length>0) {
                        // 배열에 남은게 있으면
                        self.syncTx(success, fail, fromHeight, txs);
                    } else {
                        success(fromHeight);
                    }
                }).catch(fail);
            }).catch(fail);
        }
    };
};
