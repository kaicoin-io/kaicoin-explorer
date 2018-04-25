const r = require('rethinkdb');
const config = require("./config.js");
const { GetBlockchainInfo } = require('multichain-api/Commands/GetBlockchainInfo');
const { GetBlockchainParams } = require('multichain-api/Commands/GetBlockchainParams');
const { GetInfo } = require('multichain-api/Commands/GetInfo');
const { GetBlock } = require('multichain-api/Commands/GetBlock');
const { GetMiningInfo } = require('multichain-api/Commands/GetMiningInfo');


// lastBlock -> blocknotify or... get height

module.exports = function() {

    return {
        insertPrice: function (item) {
            self = this;
            r.connect(rethinkdb, function (e, conn) {
                if (e) {
                    console.warn("could not connect to the database, " + e.message);
                    if (conn) {
                        conn.close();
                    }
                    return;
                }
                r.table(table.TB_PRICE).insert(item, {returnChanges: true}).run(conn)
                    .then(function (result) {
                        if (result.inserted !== 1) {
                            console.error("not inserted.");
                        } else {
                            console.log("inserted.");
                        }
                    }).error(function (e) {
                    onInsertError(e);
                });
            });

        },
        getPrices: function (callback) {
            var res = [];
            r.connect(rethinkdb, function (e, conn) {
                r.table(table.TB_PRICE).orderBy({index: table.PK_TB_PRICE}).run(conn)
                    .then(function (csr1) {
                        return csr1.toArray();
                    }).then(function (res1) {
                    res = res1;
                    return;
                }).finally(function () {
                    conn.close();
                    callback(res);
                });
            });
        }
    }

};
