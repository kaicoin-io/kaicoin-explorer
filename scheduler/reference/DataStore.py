
    def _init_datadirs(store):

        datadirs = {}
        for row in store.selectall("""
            SELECT datadir_id, dirname, blkfile_number, blkfile_offset,
                   chain_id
              FROM datadir"""):
            id, dir, num, offs, chain_id = row
            datadirs[dir] = {
                "id": id,
                "dirname": dir,
                "blkfile_number": int(num),
                "blkfile_offset": int(offs),
                "chain_id": None if chain_id is None else int(chain_id),
                "loader": None}


        def lookup_chain_id(name):
            row = store.selectrow(
                "SELECT chain_id FROM chain WHERE chain_name = ?",
                (name,))
            return None if row is None else int(row[0])
                        store.sql("""
                            INSERT INTO chain (
                                chain_id, chain_name, chain_code3,
                                chain_magic, chain_address_checksum, chain_address_version, chain_script_addr_vers, chain_policy,
                                chain_decimals, chain_protocol_version
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                  (chain_id, chain_name, code3,
                                   store.binin(chain_magic), store.binin(address_checksum), store.binin(addr_vers), store.binin(script_addr_vers),
# MULTICHAIN END
                                   dircfg.get('policy', chain_name), decimals, protocol_version))
                        store.commit()
                        store.log.warning("Assigned chain_id %d to %s",
                                          chain_id, chain_name)


    def init_chains(store):
        for chain_id, magic, chain_name, chain_code3, address_checksum, address_version, script_addr_vers, \
                chain_policy, chain_decimals, chain_protocol_version in \
                store.selectall("""
                    SELECT chain_id, chain_magic, chain_name, chain_code3,
                           chain_address_checksum, chain_address_version, chain_script_addr_vers, chain_policy, chain_decimals,
                           chain_protocol_version
                      FROM chain
                """):
            chain = Chain.create(
                id              = int(chain_id),
                magic           = store.binout(magic),
                name            = unicode(chain_name),
                code3           = chain_code3 and unicode(chain_code3),
                address_checksum = store.binout(address_checksum),
                protocol_version = int(chain_protocol_version),
                address_version = store.binout(address_version),
                script_addr_vers = store.binout(script_addr_vers),
                policy          = unicode(chain_policy),
                decimals        = None if chain_decimals is None else \
                    int(chain_decimals))

            # Legacy config option.
            if chain.name in no_bit8_chains and \
                    chain.has_feature('block_version_bit8_merge_mine'):
                chain = Chain.create(src=chain, policy="LegacyNoBit8")

            store.chains_by.id[chain.id] = chain
            store.chains_by.name[chain.name] = chain
            store.chains_by.magic[bytes(chain.magic)] = chain

    def get_multichain_name_by_id(store, chain_id):
        dirname = store.get_dirname_by_id( chain_id)
        if dirname is None:
            return None
        return os.path.basename(dirname)

    def get_dirname_by_id(store, chain_id):
        """
        Get the chain name of a multichain network, given the chain id.
        :param store:
        :param chain_id:
        :return:
        """
        chain_id = int(chain_id)
        row = store.selectrow("""
                SELECT dirname
                  FROM datadir
                 WHERE chain_id = ?""", (chain_id,))
        if row is None:
            return None
        dirname, = row
        return dirname

    def refresh_ddl(store):
        store._ddl = {
            "chain_summary":
# XXX I could do a lot with MATERIALIZED views.
"""CREATE VIEW chain_summary AS SELECT
    cc.chain_id,
    cc.in_longest,
    b.block_id,
    b.block_hash,
    b.block_version,
    b.block_hashMerkleRoot,
    b.block_nTime,
    b.block_nBits,
    b.block_nNonce,
    cc.block_height,
    b.prev_block_id,
    prev.block_hash prev_block_hash,
    b.block_chain_work,
    b.block_num_tx,
    b.block_value_in,
    b.block_value_out,
    b.block_total_satoshis,
    b.block_total_seconds,
    b.block_satoshi_seconds,
    b.block_total_ss,
    b.block_ss_destroyed
FROM chain_candidate cc
JOIN block b ON (cc.block_id = b.block_id)
LEFT JOIN block prev ON (b.prev_block_id = prev.block_id)""",

            "txout_detail":
"""CREATE VIEW txout_detail AS SELECT
    cc.chain_id,
    cc.in_longest,
    cc.block_id,
    b.block_hash,
    b.block_height,
    block_tx.tx_pos,
    tx.tx_id,
    tx.tx_hash,
    tx.tx_lockTime,
    tx.tx_version,
    tx.tx_size,
    txout.txout_id,
    txout.txout_pos,
    txout.txout_value,
    txout.txout_scriptPubKey,
    pubkey.pubkey_id,
    pubkey.pubkey_hash,
    pubkey.pubkey
  FROM chain_candidate cc
  JOIN block b ON (cc.block_id = b.block_id)
  JOIN block_tx ON (b.block_id = block_tx.block_id)
  JOIN tx    ON (tx.tx_id = block_tx.tx_id)
  JOIN txout ON (tx.tx_id = txout.tx_id)
  LEFT JOIN pubkey ON (txout.pubkey_id = pubkey.pubkey_id)""",

            "txin_detail":
"""CREATE VIEW txin_detail AS SELECT
    cc.chain_id,
    cc.in_longest,
    cc.block_id,
    b.block_hash,
    b.block_height,
    block_tx.tx_pos,
    tx.tx_id,
    tx.tx_hash,
    tx.tx_lockTime,
    tx.tx_version,
    tx.tx_size,
    txin.txin_id,
    txin.txin_pos,
    txin.txout_id prevout_id""" + (""",
    txin.txin_scriptSig,
    txin.txin_sequence""" if store.keep_scriptsig else """,
    NULL txin_scriptSig,
    NULL txin_sequence""") + """,
    prevout.txout_value txin_value,
    prevout.txout_scriptPubKey txin_scriptPubKey,
    pubkey.pubkey_id,
    pubkey.pubkey_hash,
    pubkey.pubkey
  FROM chain_candidate cc
  JOIN block b ON (cc.block_id = b.block_id)
  JOIN block_tx ON (b.block_id = block_tx.block_id)
  JOIN tx    ON (tx.tx_id = block_tx.tx_id)
  JOIN txin  ON (tx.tx_id = txin.tx_id)
  LEFT JOIN txout prevout ON (txin.txout_id = prevout.txout_id)
  LEFT JOIN pubkey
      ON (prevout.pubkey_id = pubkey.pubkey_id)""",

            "txout_approx":
# View of txout for drivers like sqlite3 that can not handle large
# integer arithmetic.  For them, we transform the definition of
# txout_approx_value to DOUBLE PRECISION (approximate) by a CAST.
"""CREATE VIEW txout_approx AS SELECT
    txout_id,
    tx_id,
    txout_value txout_approx_value
  FROM txout""",

"""CREATE TABLE datadir (
    datadir_id  NUMERIC(10) NOT NULL PRIMARY KEY,
    dirname     VARCHAR(2000) NOT NULL,
    blkfile_number NUMERIC(8) NULL,
    blkfile_offset NUMERIC(20) NULL,
    chain_id    NUMERIC(10) NULL
)""",

# A block of the type used by Bitcoin.
"""CREATE TABLE block (
    block_id      NUMERIC(14) NOT NULL PRIMARY KEY,
    block_hash    BINARY(32)  UNIQUE NOT NULL,
    block_version NUMERIC(10),
    block_hashMerkleRoot BINARY(32),
    block_nTime   NUMERIC(20),
    block_nBits   NUMERIC(10),
    block_nNonce  NUMERIC(10),
    block_height  NUMERIC(14) NULL,
    prev_block_id NUMERIC(14) NULL,
    search_block_id NUMERIC(14) NULL,
    block_chain_work BINARY(""" + str(WORK_BITS / 8) + """),
    block_value_in NUMERIC(30) NULL,
    block_value_out NUMERIC(30),
    block_total_satoshis NUMERIC(26) NULL,
    block_total_seconds NUMERIC(20) NULL,
    block_satoshi_seconds NUMERIC(28) NULL,
    block_total_ss NUMERIC(28) NULL,
    block_num_tx  NUMERIC(10) NOT NULL,
    block_ss_destroyed NUMERIC(28) NULL,
    FOREIGN KEY (prev_block_id)
        REFERENCES block (block_id),
    FOREIGN KEY (search_block_id)
        REFERENCES block (block_id)
)""",

# CHAIN comprises a magic number, a policy, and (indirectly via
# CHAIN_LAST_BLOCK_ID and the referenced block's ancestors) a genesis
# block, possibly null.  A chain may have a currency code.
"""CREATE TABLE chain (
    chain_id    NUMERIC(10) NOT NULL PRIMARY KEY,
    chain_name  VARCHAR(100) UNIQUE NOT NULL,
    chain_code3 VARCHAR(5)  NULL,
    chain_address_version VARBINARY(100) NOT NULL,
    chain_script_addr_vers VARBINARY(100) NULL,
    chain_address_checksum VARBINARY(100) NULL,
    chain_magic BINARY(4)     NULL,
    chain_policy VARCHAR(255) NOT NULL,
    chain_decimals NUMERIC(2) NULL,
    chain_last_block_id NUMERIC(14) NULL,
    chain_protocol_version NUMERIC(10) NOT NULL,
    FOREIGN KEY (chain_last_block_id)
        REFERENCES block (block_id)
)""",

# CHAIN_CANDIDATE lists blocks that are, or might become, part of the
# given chain.  IN_LONGEST is 1 when the block is in the chain, else 0.
# IN_LONGEST denormalizes information stored canonically in
# CHAIN.CHAIN_LAST_BLOCK_ID and BLOCK.PREV_BLOCK_ID.
"""CREATE TABLE chain_candidate (
    chain_id      NUMERIC(10) NOT NULL,
    block_id      NUMERIC(14) NOT NULL,
    in_longest    NUMERIC(1),
    block_height  NUMERIC(14),
    PRIMARY KEY (chain_id, block_id),
    FOREIGN KEY (block_id) REFERENCES block (block_id)
)""",

# An orphan block must remember its hashPrev.
"""CREATE TABLE orphan_block (
    block_id      NUMERIC(14) NOT NULL PRIMARY KEY,
    block_hashPrev BINARY(32) NOT NULL,
    FOREIGN KEY (block_id) REFERENCES block (block_id)
)""",
"""CREATE INDEX x_orphan_block_hashPrev ON orphan_block (block_hashPrev)""",

# Denormalize the relationship inverse to BLOCK.PREV_BLOCK_ID.
"""CREATE TABLE block_next (
    block_id      NUMERIC(14) NOT NULL,
    next_block_id NUMERIC(14) NOT NULL,
    PRIMARY KEY (block_id, next_block_id),
    FOREIGN KEY (block_id) REFERENCES block (block_id),
    FOREIGN KEY (next_block_id) REFERENCES block (block_id)
)""",

# A transaction of the type used by Bitcoin.
"""CREATE TABLE tx (
    tx_id         NUMERIC(26) NOT NULL PRIMARY KEY,
    tx_hash       BINARY(32)  UNIQUE NOT NULL,
    tx_version    NUMERIC(10),
    tx_lockTime   NUMERIC(10),
    tx_size       NUMERIC(10)
)""",

# Presence of transactions in blocks is many-to-many.
"""CREATE TABLE block_tx (
    block_id      NUMERIC(14) NOT NULL,
    tx_id         NUMERIC(26) NOT NULL,
    tx_pos        NUMERIC(10) NOT NULL,
    PRIMARY KEY (block_id, tx_id),
    UNIQUE (block_id, tx_pos),
    FOREIGN KEY (block_id)
        REFERENCES block (block_id),
    FOREIGN KEY (tx_id)
        REFERENCES tx (tx_id)
)""",
"""CREATE INDEX x_block_tx_tx ON block_tx (tx_id)""",

# A public key for sending bitcoins.  PUBKEY_HASH is derivable from a
# Bitcoin or Testnet address.
"""CREATE TABLE pubkey (
    pubkey_id     NUMERIC(26) NOT NULL PRIMARY KEY,
    pubkey_hash   BINARY(20)  UNIQUE NOT NULL,
    pubkey        VARBINARY(""" + str(MAX_PUBKEY) + """) NULL,
    pubkey_flags  NUMERIC(32) NULL
)""",

"""CREATE TABLE multisig_pubkey (
    multisig_id   NUMERIC(26) NOT NULL,
    pubkey_id     NUMERIC(26) NOT NULL,
    PRIMARY KEY (multisig_id, pubkey_id),
    FOREIGN KEY (multisig_id) REFERENCES pubkey (pubkey_id),
    FOREIGN KEY (pubkey_id) REFERENCES pubkey (pubkey_id)
)""",
"""CREATE INDEX x_multisig_pubkey_pubkey ON multisig_pubkey (pubkey_id)""",

# A transaction out-point.
"""CREATE TABLE txout (
    txout_id      NUMERIC(26) NOT NULL PRIMARY KEY,
    tx_id         NUMERIC(26) NOT NULL,
    txout_pos     NUMERIC(10) NOT NULL,
    txout_value   NUMERIC(30) NOT NULL,
    txout_scriptPubKey VARBINARY(""" + str(MAX_SCRIPT) + """),
    pubkey_id     NUMERIC(26),
    UNIQUE (tx_id, txout_pos),
    FOREIGN KEY (pubkey_id)
        REFERENCES pubkey (pubkey_id)
)""",
"""CREATE INDEX x_txout_pubkey ON txout (pubkey_id)""",

# A transaction in-point.
"""CREATE TABLE txin (
    txin_id       NUMERIC(26) NOT NULL PRIMARY KEY,
    tx_id         NUMERIC(26) NOT NULL,
    txin_pos      NUMERIC(10) NOT NULL,
    txout_id      NUMERIC(26)""" + (""",
    txin_scriptSig VARBINARY(""" + str(MAX_SCRIPT) + """),
    txin_sequence NUMERIC(10)""" if store.keep_scriptsig else "") + """,
    UNIQUE (tx_id, txin_pos),
    FOREIGN KEY (tx_id)
        REFERENCES tx (tx_id)
)""",
"""CREATE INDEX x_txin_txout ON txin (txout_id)""",

# While TXIN.TXOUT_ID can not be found, we must remember TXOUT_POS,
# a.k.a. PREVOUT_N.
"""CREATE TABLE unlinked_txin (
    txin_id       NUMERIC(26) NOT NULL PRIMARY KEY,
    txout_tx_hash BINARY(32)  NOT NULL,
    txout_pos     NUMERIC(10) NOT NULL,
    FOREIGN KEY (txin_id) REFERENCES txin (txin_id)
)""",
"""CREATE INDEX x_unlinked_txin_outpoint
    ON unlinked_txin (txout_tx_hash, txout_pos)""",

"""CREATE TABLE block_txin (
    block_id      NUMERIC(14) NOT NULL,
    txin_id       NUMERIC(26) NOT NULL,
    out_block_id  NUMERIC(14) NOT NULL,
    PRIMARY KEY (block_id, txin_id),
    FOREIGN KEY (block_id) REFERENCES block (block_id),
    FOREIGN KEY (txin_id) REFERENCES txin (txin_id),
    FOREIGN KEY (out_block_id) REFERENCES block (block_id)
)""",


# issued assets are stored here
# op_drop has issue qty
# op_return of issue asset has: name, multiplier
# 2 steps to get all data.
"""CREATE TABLE asset (
    asset_id      NUMERIC(10) NOT NULL PRIMARY KEY,
    tx_id         NUMERIC(26) NOT NULL,
    chain_id      NUMERIC(10) NOT NULL,
    name          VARCHAR(255) NOT NULL,
    multiplier    NUMERIC(10) NOT NULL,
    issue_qty     NUMERIC(30) NOT NULL,
    prefix        NUMERIC(10) NOT NULL,
    UNIQUE      (tx_id),
    FOREIGN KEY (tx_id) REFERENCES tx (tx_id),
    FOREIGN KEY (chain_id) REFERENCES chain (chain_id)
)""",

"""CREATE TABLE asset_txid (
    asset_id      NUMERIC(10) NOT NULL,
    tx_id         NUMERIC(26) NOT NULL,
    txout_pos     NUMERIC(10) NOT NULL,
    UNIQUE (asset_id, tx_id, txout_pos),
    FOREIGN KEY (tx_id) REFERENCES tx (tx_id),
    FOREIGN KEY (asset_id) REFERENCES asset (asset_id)
)""",

# raw units
"""CREATE TABLE asset_address_balance (
    asset_id      NUMERIC(10) NOT NULL,
    pubkey_id     NUMERIC(26) NOT NULL,
    balance       NUMERIC(30) NOT NULL,
    PRIMARY KEY (asset_id, pubkey_id),
    FOREIGN KEY (asset_id) REFERENCES asset (asset_id),
    FOREIGN KEY (pubkey_id) REFERENCES pubkey (pubkey_id)
)""",


        store.sql("""
            INSERT INTO pubkey (pubkey_id, pubkey_hash) VALUES (?, ?)""",
                  (NULL_PUBKEY_ID, store.binin(NULL_PUBKEY_HASH)))

        if store.args.use_firstbits:
            store.config['use_firstbits'] = "true"
            store.ddl(
                """CREATE TABLE abe_firstbits (
                    pubkey_id       NUMERIC(26) NOT NULL,
                    block_id        NUMERIC(14) NOT NULL,
                    address_version VARBINARY(10) NOT NULL,
                    firstbits       VARCHAR(50) NOT NULL,
                    PRIMARY KEY (address_version, pubkey_id, block_id),
                    FOREIGN KEY (pubkey_id) REFERENCES pubkey (pubkey_id),
                    FOREIGN KEY (block_id) REFERENCES block (block_id)
                )""")
            store.ddl(
                """CREATE INDEX x_abe_firstbits
                    ON abe_firstbits (address_version, firstbits)""")
        else:
            store.config['use_firstbits'] = "false"

        store.config['keep_scriptsig'] = \
            "true" if store.args.keep_scriptsig else "false"

        store.save_config()
        store.commit()

    def insert_chain(store, chain):
        chain.id = store.new_id("chain")

        store.sql("""
            INSERT INTO chain (
                chain_id, chain_magic, chain_name, chain_code3,
                chain_address_checksum, chain_address_version, chain_script_addr_vers, chain_policy, chain_decimals,
                chain_protocol_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (chain.id, store.binin(chain.magic), chain.name,
                   chain.code3, store.binin(chain.address_checksum), store.binin(chain.address_version), store.binin(chain.script_addr_vers),
                   chain.policy, chain.decimals, chain.protocol_version))

    def cache_block(store, block_id, height, prev_id, search_id):
        assert isinstance(block_id, int), block_id
        assert isinstance(height, int), height
        assert prev_id is None or isinstance(prev_id, int)
        assert search_id is None or isinstance(search_id, int)
        block = {
            'height':    height,
            'prev_id':   prev_id,
            'search_id': search_id}
        store._blocks[block_id] = block
        return block

    def _load_block(store, block_id):
        block = store._blocks.get(block_id)
        if block is None:
            row = store.selectrow("""
                SELECT block_height, prev_block_id, search_block_id
                  FROM block
                 WHERE block_id = ?""", (block_id,))
            if row is None:
                return None
            height, prev_id, search_id = row
            block = store.cache_block(
                block_id, int(height),
                None if prev_id is None else int(prev_id),
                None if search_id is None else int(search_id))
        return block

    def get_block_id_at_height(store, height, descendant_id):
        if height is None:
            return None
        while True:
            block = store._load_block(descendant_id)
            if block['height'] == height:
                return descendant_id
            descendant_id = block[
                'search_id'
                if util.get_search_height(block['height']) >= height else
                'prev_id']

    def is_descended_from(store, block_id, ancestor_id):
#        ret = store._is_descended_from(block_id, ancestor_id)
#        store.log.debug("%d is%s descended from %d", block_id, '' if ret else ' NOT', ancestor_id)
#        return ret
#    def _is_descended_from(store, block_id, ancestor_id):
        block = store._load_block(block_id)
        ancestor = store._load_block(ancestor_id)
        height = ancestor['height']
        return block['height'] >= height and \
            store.get_block_id_at_height(height, block_id) == ancestor_id

    def get_block_height(store, block_id):
        return store._load_block(int(block_id))['height']

    def find_prev(store, hash):
        row = store.selectrow("""
            SELECT block_id, block_height, block_chain_work,
                   block_total_satoshis, block_total_seconds,
                   block_satoshi_seconds, block_total_ss, block_nTime
              FROM block
             WHERE block_hash=?""", (store.hashin(hash),))
        if row is None:
            return (None, None, None, None, None, None, None, None)
        (id, height, chain_work, satoshis, seconds, satoshi_seconds,
         total_ss, nTime) = row
        return (id, None if height is None else int(height),
                store.binout_int(chain_work),
                None if satoshis is None else int(satoshis),
                None if seconds is None else int(seconds),
                None if satoshi_seconds is None else int(satoshi_seconds),
                None if total_ss is None else int(total_ss),
                int(nTime))

    def import_block(store, b, chain_ids=None, chain=None):

        # Import new transactions.

        if chain_ids is None:
            chain_ids = frozenset() if chain is None else frozenset([chain.id])

        b['value_in'] = 0
        b['value_out'] = 0
        b['value_destroyed'] = 0
        tx_hash_array = []

        # In the common case, all the block's txins _are_ linked, and we
        # can avoid a query if we notice this.
        all_txins_linked = True

        for pos in xrange(len(b['transactions'])):
            tx = b['transactions'][pos]

            if 'hash' not in tx:
                if chain is None:
                    store.log.debug("Falling back to SHA256 transaction hash")
                    tx['hash'] = util.double_sha256(tx['__data__'])
                else:
                    tx['hash'] = chain.transaction_hash(tx['__data__'])

            tx_hash_array.append(tx['hash'])
            tx['tx_id'] = store.tx_find_id_and_value(tx, pos == 0)

            if tx['tx_id']:
                all_txins_linked = False
            else:
                if store.commit_bytes == 0:
                    tx['tx_id'] = store.import_and_commit_tx(tx, pos == 0, chain)
                else:
                    tx['tx_id'] = store.import_tx(tx, pos == 0, chain)
                if tx.get('unlinked_count', 1) > 0:
                    all_txins_linked = False

            if tx['value_in'] is None:
                b['value_in'] = None
            elif b['value_in'] is not None:
                b['value_in'] += tx['value_in']
            b['value_out'] += tx['value_out']
            b['value_destroyed'] += tx['value_destroyed']

        # Get a new block ID.
        block_id = int(store.new_id("block"))
        b['block_id'] = block_id

        if chain is not None:
            # Verify Merkle root.
            if b['hashMerkleRoot'] != chain.merkle_root(tx_hash_array):
                raise MerkleRootMismatch(b['hash'], tx_hash_array)

        # Look for the parent block.
        hashPrev = b['hashPrev']
        if chain is None:
            # XXX No longer used.
            is_genesis = hashPrev == util.GENESIS_HASH_PREV
        else:
            is_genesis = hashPrev == chain.genesis_hash_prev

        (prev_block_id, prev_height, prev_work, prev_satoshis,
         prev_seconds, prev_ss, prev_total_ss, prev_nTime) = (
            (None, -1, 0, 0, 0, 0, 0, b['nTime'])
            if is_genesis else
            store.find_prev(hashPrev))

        b['prev_block_id'] = prev_block_id
        b['height'] = None if prev_height is None else prev_height + 1
        b['chain_work'] = util.calculate_work(prev_work, b['nBits'])

        if prev_seconds is None:
            b['seconds'] = None
        else:
            b['seconds'] = prev_seconds + b['nTime'] - prev_nTime
        if prev_satoshis is None or prev_satoshis < 0 or b['value_in'] is None:
            # XXX Abuse this field to save work in adopt_orphans.
            b['satoshis'] = -1 - b['value_destroyed']
        else:
            b['satoshis'] = prev_satoshis + b['value_out'] - b['value_in'] \
                - b['value_destroyed']

        if prev_satoshis is None or prev_satoshis < 0:
            ss_created = None
            b['total_ss'] = None
        else:
            ss_created = prev_satoshis * (b['nTime'] - prev_nTime)
            b['total_ss'] = prev_total_ss + ss_created

        if b['height'] is None or b['height'] < 2:
            b['search_block_id'] = None
        else:
            b['search_block_id'] = store.get_block_id_at_height(
                util.get_search_height(int(b['height'])),
                None if prev_block_id is None else int(prev_block_id))

        # Insert the block table row.
        try:
            store.sql(
                """INSERT INTO block (
                    block_id, block_hash, block_version, block_hashMerkleRoot,
                    block_nTime, block_nBits, block_nNonce, block_height,
                    prev_block_id, block_chain_work, block_value_in,
                    block_value_out, block_total_satoshis,
                    block_total_seconds, block_total_ss, block_num_tx,
                    search_block_id
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )""",
                (block_id, store.hashin(b['hash']), store.intin(b['version']),
                 store.hashin(b['hashMerkleRoot']), store.intin(b['nTime']),
                 store.intin(b['nBits']), store.intin(b['nNonce']),
                 b['height'], prev_block_id,
                 store.binin_int(b['chain_work'], WORK_BITS),
                 store.intin(b['value_in']), store.intin(b['value_out']),
                 store.intin(b['satoshis']), store.intin(b['seconds']),
                 store.intin(b['total_ss']),
                 len(b['transactions']), b['search_block_id']))

        except store.dbmodule.DatabaseError:

            if store.commit_bytes == 0:
                # Rollback won't undo any previous changes, since we
                # always commit.
                store.rollback()
                # If the exception is due to another process having
                # inserted the same block, it is okay.
                row = store.selectrow("""
                    SELECT block_id, block_satoshi_seconds
                      FROM block
                     WHERE block_hash = ?""",
                    (store.hashin(b['hash']),))
                if row:
                    store.log.info("Block already inserted; block_id %d unsued",
                                   block_id)
                    b['block_id'] = int(row[0])
                    b['ss'] = None if row[1] is None else int(row[1])
                    store.offer_block_to_chains(b, chain_ids)
                    return

            # This is not an expected error, or our caller may have to
            # rewind a block file.  Let them deal with it.
            raise

        # List the block's transactions in block_tx.
        for tx_pos in xrange(len(b['transactions'])):
            tx = b['transactions'][tx_pos]
            store.sql("""
                INSERT INTO block_tx
                    (block_id, tx_id, tx_pos)
                VALUES (?, ?, ?)""",
                      (block_id, tx['tx_id'], tx_pos))
            store.log.info("block_tx %d %d", block_id, tx['tx_id'])

        if b['height'] is not None:
            store._populate_block_txin(block_id)

            if all_txins_linked or not store._has_unlinked_txins(block_id):
                b['ss_destroyed'] = store._get_block_ss_destroyed(
                    block_id, b['nTime'],
                    map(lambda tx: tx['tx_id'], b['transactions']))
                if ss_created is None or prev_ss is None:
                    b['ss'] = None
                else:
                    b['ss'] = prev_ss + ss_created - b['ss_destroyed']

                store.sql("""
                    UPDATE block
                       SET block_satoshi_seconds = ?,
                           block_ss_destroyed = ?
                     WHERE block_id = ?""",
                          (store.intin(b['ss']),
                           store.intin(b['ss_destroyed']),
                           block_id))
            else:
                b['ss_destroyed'] = None
                b['ss'] = None

        # Store the inverse hashPrev relationship or mark the block as
        # an orphan.
        if prev_block_id:
            store.sql("""
                INSERT INTO block_next (block_id, next_block_id)
                VALUES (?, ?)""", (prev_block_id, block_id))
        elif not is_genesis:
            store.sql("INSERT INTO orphan_block (block_id, block_hashPrev)" +
                      " VALUES (?, ?)", (block_id, store.hashin(b['hashPrev'])))

        for row in store.selectall("""
            SELECT block_id FROM orphan_block WHERE block_hashPrev = ?""",
                                   (store.hashin(b['hash']),)):
            (orphan_id,) = row
            store.sql("UPDATE block SET prev_block_id = ? WHERE block_id = ?",
                      (block_id, orphan_id))
            store.sql("""
                INSERT INTO block_next (block_id, next_block_id)
                VALUES (?, ?)""", (block_id, orphan_id))
            store.sql("DELETE FROM orphan_block WHERE block_id = ?",
                      (orphan_id,))

        # offer_block_to_chains calls adopt_orphans, which propagates
        # block_height and other cumulative data to the blocks
        # attached above.
        store.offer_block_to_chains(b, chain_ids)

        return block_id

    def _populate_block_txin(store, block_id):
        # Create rows in block_txin.  In case of duplicate transactions,
        # choose the one with the lowest block ID.  XXX For consistency,
        # it should be the lowest height instead of block ID.
        for row in store.selectall("""
            SELECT txin.txin_id, MIN(obt.block_id)
              FROM block_tx bt
              JOIN txin ON (txin.tx_id = bt.tx_id)
              JOIN txout ON (txin.txout_id = txout.txout_id)
              JOIN block_tx obt ON (txout.tx_id = obt.tx_id)
              JOIN block ob ON (obt.block_id = ob.block_id)
             WHERE bt.block_id = ?
               AND ob.block_chain_work IS NOT NULL
             GROUP BY txin.txin_id""", (block_id,)):
            (txin_id, oblock_id) = row
            if store.is_descended_from(block_id, int(oblock_id)):
                store.sql("""
                    INSERT INTO block_txin (block_id, txin_id, out_block_id)
                    VALUES (?, ?, ?)""",
                          (block_id, txin_id, oblock_id))

    def _has_unlinked_txins(store, block_id):
        (unlinked_count,) = store.selectrow("""
            SELECT COUNT(1)
              FROM block_tx bt
              JOIN txin ON (bt.tx_id = txin.tx_id)
              JOIN unlinked_txin u ON (txin.txin_id = u.txin_id)
             WHERE bt.block_id = ?""", (block_id,))
        return unlinked_count > 0

    def _get_block_ss_destroyed(store, block_id, nTime, tx_ids):
        block_ss_destroyed = 0
        for tx_id in tx_ids:
            destroyed = int(store.selectrow("""
                SELECT COALESCE(SUM(txout_approx.txout_approx_value *
                                    (? - b.block_nTime)), 0)
                  FROM block_txin bti
                  JOIN txin ON (bti.txin_id = txin.txin_id)
                  JOIN txout_approx ON (txin.txout_id = txout_approx.txout_id)
                  JOIN block_tx obt ON (txout_approx.tx_id = obt.tx_id)
                  JOIN block b ON (obt.block_id = b.block_id)
                 WHERE bti.block_id = ? AND txin.tx_id = ?""",
                                            (nTime, block_id, tx_id))[0])
            block_ss_destroyed += destroyed
        return block_ss_destroyed

    # Propagate cumulative values to descendant blocks.  Return info
    # about the longest chains containing b.  The returned dictionary
    # is keyed by the chain_id of a chain whose validation policy b
    # satisfies.  Each value is a pair (block, work) where block is
    # the best block descended from b in the given chain, and work is
    # the sum of orphan_work and the work between b and block.  Only
    # chains in chain_mask are considered.  Even if no known chain
    # contains b, this routine populates any descendant blocks'
    # cumulative statistics that are known for b and returns an empty
    # dictionary.
    def adopt_orphans(store, b, orphan_work, chain_ids, chain_mask):

        # XXX As originally written, this function occasionally hit
        # Python's recursion limit.  I am rewriting it iteratively
        # with minimal changes, hence the odd style.  Guido is
        # particularly unhelpful here, rejecting even labeled loops.

        ret = [None]
        def receive(x):
            ret[0] = x
        def doit():
            store._adopt_orphans_1(stack)
        stack = [receive, chain_mask, chain_ids, orphan_work, b, doit]
        while stack:
            stack.pop()()
        return ret[0]

    def _adopt_orphans_1(store, stack):
        def doit():
            store._adopt_orphans_1(stack)
        def continuation(x):
            store._adopt_orphans_2(stack, x)
        def didit():
            ret = stack.pop()
            stack.pop()(ret)

        b = stack.pop()
        orphan_work = stack.pop()
        chain_ids = stack.pop()
        chain_mask = stack.pop()
        ret = {}
        stack += [ ret, didit ]

        block_id = b['block_id']
        height = None if b['height'] is None else int(b['height'] + 1)

        # If adding block b, b will not yet be in chain_candidate, so
        # we rely on the chain_ids argument.  If called recursively,
        # look up chain_ids in chain_candidate.
        if not chain_ids:
            if chain_mask:
                chain_mask = chain_mask.intersection(
                    store.find_chains_containing_block(block_id))
            chain_ids = chain_mask

        for chain_id in chain_ids:
            ret[chain_id] = (b, orphan_work)

        for row in store.selectall("""
            SELECT bn.next_block_id, b.block_nBits,
                   b.block_value_out, b.block_value_in, b.block_nTime,
                   b.block_total_satoshis
              FROM block_next bn
              JOIN block b ON (bn.next_block_id = b.block_id)
             WHERE bn.block_id = ?""", (block_id,)):
            next_id, nBits, value_out, value_in, nTime, satoshis = row
            nBits = int(nBits)
            nTime = int(nTime)
            satoshis = None if satoshis is None else int(satoshis)
            new_work = util.calculate_work(orphan_work, nBits)

            if b['chain_work'] is None:
                chain_work = None
            else:
                chain_work = b['chain_work'] + new_work - orphan_work

            if value_in is None:
                value, count1, count2 = store.selectrow("""
                    SELECT SUM(txout.txout_value),
                           COUNT(1),
                           COUNT(txout.txout_value)
                      FROM block_tx bt
                      JOIN txin ON (bt.tx_id = txin.tx_id)
                      LEFT JOIN txout ON (txout.txout_id = txin.txout_id)
                     WHERE bt.block_id = ?""", (next_id,))
                if count1 == count2 + 1:
                    value_in = int(value)
                else:
                    store.log.warning(
                        "not updating block %d value_in: %s != %s + 1",
                        next_id, repr(count1), repr(count2))
            else:
                value_in = int(value_in)
            generated = None if value_in is None else int(value_out - value_in)

            if b['seconds'] is None:
                seconds = None
                total_ss = None
            else:
                new_seconds = nTime - b['nTime']
                seconds = b['seconds'] + new_seconds
                if b['total_ss'] is None or b['satoshis'] is None:
                    total_ss = None
                else:
                    total_ss = b['total_ss'] + new_seconds * b['satoshis']

            if satoshis < 0 and b['satoshis'] is not None and \
                    b['satoshis'] >= 0 and generated is not None:
                satoshis += 1 + b['satoshis'] + generated

            if height is None or height < 2:
                search_block_id = None
            else:
                search_block_id = store.get_block_id_at_height(
                    util.get_search_height(height), int(block_id))

            store.sql("""
                UPDATE block
                   SET block_height = ?,
                       block_chain_work = ?,
                       block_value_in = ?,
                       block_total_seconds = ?,
                       block_total_satoshis = ?,
                       block_total_ss = ?,
                       search_block_id = ?
                 WHERE block_id = ?""",
                      (height, store.binin_int(chain_work, WORK_BITS),
                       store.intin(value_in),
                       store.intin(seconds), store.intin(satoshis),
                       store.intin(total_ss), search_block_id,
                       next_id))

            ss = None

            if height is not None:
                store.sql("""
                    UPDATE chain_candidate SET block_height = ?
                     WHERE block_id = ?""",
                    (height, next_id))

                store._populate_block_txin(int(next_id))

                if b['ss'] is None or store._has_unlinked_txins(next_id):
                    pass
                else:
                    tx_ids = map(
                        lambda row: row[0],
                        store.selectall("""
                            SELECT tx_id
                              FROM block_tx
                             WHERE block_id = ?""", (next_id,)))
                    destroyed = store._get_block_ss_destroyed(
                        next_id, nTime, tx_ids)
                    ss = b['ss'] + b['satoshis'] * (nTime - b['nTime']) \
                        - destroyed

                    store.sql("""
                        UPDATE block
                           SET block_satoshi_seconds = ?,
                               block_ss_destroyed = ?
                         WHERE block_id = ?""",
                              (store.intin(ss),
                               store.intin(destroyed),
                               next_id))

                if store.use_firstbits:
                    for (addr_vers,) in store.selectall("""
                        SELECT c.chain_address_version
                          FROM chain c
                          JOIN chain_candidate cc ON (c.chain_id = cc.chain_id)
                         WHERE cc.block_id = ?""", (next_id,)):
                        store.do_vers_firstbits(addr_vers, int(next_id))

            nb = {
                "block_id": next_id,
                "height": height,
                "chain_work": chain_work,
                "nTime": nTime,
                "seconds": seconds,
                "satoshis": satoshis,
                "total_ss": total_ss,
                "ss": ss}

            stack += [ret, continuation,
                      chain_mask, None, new_work, nb, doit]

    def _adopt_orphans_2(store, stack, next_ret):
        ret = stack.pop()
        for chain_id in ret.keys():
            pair = next_ret[chain_id]
            if pair and pair[1] > ret[chain_id][1]:
                ret[chain_id] = pair

    def _export_scriptPubKey(store, txout, chain, scriptPubKey):
        """In txout, set script_type, address_version, binaddr, and for multisig, required_signatures."""

        if scriptPubKey is None:
            txout['script_type'] = None
            txout['binaddr'] = None
            txout['address_version'] = None
            return

        script_type, data = chain.parse_txout_script(scriptPubKey)
        txout['script_type'] = script_type
        txout['address_version'] = chain.address_version

        if script_type == Chain.SCRIPT_TYPE_PUBKEY:
            txout['binaddr'] = chain.pubkey_hash(data)
        elif script_type == Chain.SCRIPT_TYPE_ADDRESS:
            txout['binaddr'] = data
        elif script_type == Chain.SCRIPT_TYPE_P2SH:
            txout['address_version'] = chain.script_addr_vers
            txout['binaddr'] = data
        elif script_type == Chain.SCRIPT_TYPE_MULTISIG:
            txout['required_signatures'] = data['m']
            txout['binaddr'] = chain.pubkey_hash(scriptPubKey)
            txout['subbinaddr'] = [
                chain.pubkey_hash(pubkey)
                for pubkey in data['pubkeys']
                ]
        elif script_type == Chain.SCRIPT_TYPE_BURN:
            txout['binaddr'] = NULL_PUBKEY_HASH
        # MULTICHAIN START
        elif script_type == Chain.SCRIPT_TYPE_MULTICHAIN:
            txout['binaddr'] = data
        elif script_type == Chain.SCRIPT_TYPE_MULTICHAIN_P2SH:
            txout['address_version'] = chain.script_addr_vers
            txout['binaddr'] = data
        elif script_type == Chain.SCRIPT_TYPE_MULTICHAIN_ENTITY_PERMISSION:
            txout['binaddr'] = data['pubkey_hash']
        # MULTICHAIN END
        else:
            txout['binaddr'] = None

    def export_block(store, chain=None, block_hash=None, block_number=None):
        """
        Return a dict with the following:

        * chain_candidates[]
            * chain
            * in_longest
        * chain_satoshis
        * chain_satoshi_seconds
        * chain_work
        * fees
        * generated
        * hash
        * hashMerkleRoot
        * hashPrev
        * height
        * nBits
        * next_block_hashes
        * nNonce
        * nTime
        * satoshis_destroyed
        * satoshi_seconds
        * transactions[]
            * fees
            * hash
            * in[]
                * address_version
                * binaddr
                * value
            * out[]
                * address_version
                * binaddr
                * value
            * size
        * value_out
        * version

        Additionally, for multisig inputs and outputs:

        * subbinaddr[]
        * required_signatures

        Additionally, for proof-of-stake chains:

        * is_proof_of_stake
        * proof_of_stake_generated
        """

        if block_number is None and block_hash is None:
            raise ValueError("export_block requires either block_hash or block_number")

        where = []
        bind = []

        if chain is not None:
            where.append('chain_id = ?')
            bind.append(chain.id)

        if block_hash is not None:
            where.append('block_hash = ?')
            bind.append(store.hashin_hex(block_hash))

        if block_number is not None:
            where.append('block_height = ? AND in_longest = 1')
            bind.append(block_number)

        sql = """
            SELECT
                chain_id,
                in_longest,
                block_id,
                block_hash,
                block_version,
                block_hashMerkleRoot,
                block_nTime,
                block_nBits,
                block_nNonce,
                block_height,
                prev_block_hash,
                block_chain_work,
                block_value_in,
                block_value_out,
                block_total_satoshis,
                block_total_seconds,
                block_satoshi_seconds,
                block_total_ss,
                block_ss_destroyed,
                block_num_tx
              FROM chain_summary
             WHERE """ + ' AND '.join(where) + """
             ORDER BY
                in_longest DESC,
                chain_id DESC"""
        rows = store.selectall(sql, bind)

        if len(rows) == 0:
            return None

        row = rows[0][2:]
        def parse_cc(row):
            chain_id, in_longest = row[:2]
            return { "chain": store.get_chain_by_id(chain_id), "in_longest": in_longest }

        # Absent the chain argument, default to highest chain_id, preferring to avoid side chains.
        cc = map(parse_cc, rows)

        # "chain" may be None, but "found_chain" will not.
        found_chain = chain
        if found_chain is None:
            if len(cc) > 0:
                found_chain = cc[0]['chain']
            else:
                # Should not normally get here.
                found_chain = store.get_default_chain()

        (block_id, block_hash, block_version, hashMerkleRoot,
         nTime, nBits, nNonce, height,
         prev_block_hash, block_chain_work, value_in, value_out,
         satoshis, seconds, ss, total_ss, destroyed, num_tx) = (
            row[0], store.hashout_hex(row[1]), row[2],
            store.hashout_hex(row[3]), row[4], int(row[5]), row[6],
            row[7], store.hashout_hex(row[8]),
            store.binout_int(row[9]), int(row[10]), int(row[11]),
            None if row[12] is None else int(row[12]),
            None if row[13] is None else int(row[13]),
            None if row[14] is None else int(row[14]),
            None if row[15] is None else int(row[15]),
            None if row[16] is None else int(row[16]),
            int(row[17]),
            )

        next_hashes = [
            store.hashout_hex(hash) for hash, il in
            store.selectall("""
            SELECT DISTINCT n.block_hash, cc.in_longest
              FROM block_next bn
              JOIN block n ON (bn.next_block_id = n.block_id)
              JOIN chain_candidate cc ON (n.block_id = cc.block_id)
             WHERE bn.block_id = ?
             ORDER BY cc.in_longest DESC""",
                            (block_id,)) ]

        tx_ids = []
        txs = {}
        block_out = 0
        block_in = 0

        for row in store.selectall("""
            SELECT tx_id, tx_hash, tx_size, txout_value, txout_scriptPubKey
              FROM txout_detail
             WHERE block_id = ?
             ORDER BY tx_pos, txout_pos
        """, (block_id,)):
            tx_id, tx_hash, tx_size, txout_value, scriptPubKey = (
                row[0], row[1], row[2], int(row[3]), store.binout(row[4]))
            tx = txs.get(tx_id)
            if tx is None:
                tx_ids.append(tx_id)
                txs[tx_id] = {
                    "hash": store.hashout_hex(tx_hash),
                    "total_out": 0,
                    "total_in": 0,
                    "out": [],
                    "in": [],
                    "size": int(tx_size),
                    }
                tx = txs[tx_id]
            tx['total_out'] += txout_value
            block_out += txout_value

            txout = { 'value': txout_value }
            store._export_scriptPubKey(txout, found_chain, scriptPubKey)
            tx['out'].append(txout)

        for row in store.selectall("""
            SELECT tx_id, txin_value, txin_scriptPubKey
              FROM txin_detail
             WHERE block_id = ?
             ORDER BY tx_pos, txin_pos
        """, (block_id,)):
            tx_id, txin_value, scriptPubKey = (
                row[0], 0 if row[1] is None else int(row[1]),
                store.binout(row[2]))
            tx = txs.get(tx_id)
            if tx is None:
                # Strange, inputs but no outputs?
                tx_ids.append(tx_id)
                tx_hash, tx_size = store.selectrow("""
                    SELECT tx_hash, tx_size FROM tx WHERE tx_id = ?""",
                                           (tx_id,))
                txs[tx_id] = {
                    "hash": store.hashout_hex(tx_hash),
                    "total_out": 0,
                    "total_in": 0,
                    "out": [],
                    "in": [],
                    "size": int(tx_size),
                    }
                tx = txs[tx_id]
            tx['total_in'] += txin_value
            block_in += txin_value

            txin = { 'value': txin_value }
            store._export_scriptPubKey(txin, found_chain, scriptPubKey)
            tx['in'].append(txin)

        generated = block_out - block_in
        coinbase_tx = txs[tx_ids[0]]
        coinbase_tx['fees'] = 0
        block_fees = coinbase_tx['total_out'] - generated

        b = {
            'chain_candidates':      cc,
            'chain_satoshis':        satoshis,
            'chain_satoshi_seconds': total_ss,
            'chain_work':            block_chain_work,
            'fees':                  block_fees,
            'generated':             generated,
            'hash':                  block_hash,
            'hashMerkleRoot':        hashMerkleRoot,
            'hashPrev':              prev_block_hash,
            'height':                height,
            'nBits':                 nBits,
            'next_block_hashes':     next_hashes,
            'nNonce':                nNonce,
            'nTime':                 nTime,
            'satoshis_destroyed':    destroyed,
            'satoshi_seconds':       ss,
            'transactions':          [txs[tx_id] for tx_id in tx_ids],
            'value_out':             block_out,
            'version':               block_version,
            }

        is_stake_chain = chain is not None and chain.has_feature('nvc_proof_of_stake')
        if is_stake_chain:
            # Proof-of-stake display based loosely on CryptoManiac/novacoin and
            # http://nvc.cryptocoinexplorer.com.
            b['is_proof_of_stake'] = len(tx_ids) > 1 and coinbase_tx['total_out'] == 0

        for tx_id in tx_ids[1:]:
            tx = txs[tx_id]
            tx['fees'] = tx['total_in'] - tx['total_out']

        if is_stake_chain and b['is_proof_of_stake']:
            b['proof_of_stake_generated'] = -txs[tx_ids[1]]['fees']
            txs[tx_ids[1]]['fees'] = 0
            b['fees'] += b['proof_of_stake_generated']

        return b

    def tx_find_id_and_value(store, tx, is_coinbase, check_only=False):
        row = store.selectrow("""
            SELECT tx.tx_id, SUM(txout.txout_value), SUM(
                       CASE WHEN txout.pubkey_id > 0 THEN txout.txout_value
                            ELSE 0 END)
              FROM tx
              LEFT JOIN txout ON (tx.tx_id = txout.tx_id)
             WHERE tx_hash = ?
             GROUP BY tx.tx_id""",
                              (store.hashin(tx['hash']),))
        if row:
            if check_only:
                 # Don't update tx, saves a statement when all we care is
                 # whenever tx_id is in store
                 return row[0]

            tx_id, value_out, undestroyed = row
            value_out = 0 if value_out is None else int(value_out)
            undestroyed = 0 if undestroyed is None else int(undestroyed)
            count_in, value_in = store.selectrow("""
                SELECT COUNT(1), SUM(prevout.txout_value)
                  FROM txin
                  JOIN txout prevout ON (txin.txout_id = prevout.txout_id)
                 WHERE txin.tx_id = ?""", (tx_id,))
            if (count_in or 0) < len(tx['txIn']):
                value_in = 0 if is_coinbase else None
            tx['value_in'] = None if value_in is None else int(value_in)
            tx['value_out'] = value_out
            tx['value_destroyed'] = value_out - undestroyed
            return tx_id

        return None

    def import_tx(store, tx, is_coinbase, chain):
        tx_id = store.new_id("tx")
        dbhash = store.hashin(tx['hash'])

        if 'size' not in tx:
            tx['size'] = len(tx['__data__'])

        store.sql("""
            INSERT INTO tx (tx_id, tx_hash, tx_version, tx_lockTime, tx_size)
            VALUES (?, ?, ?, ?, ?)""",
                  (tx_id, dbhash, store.intin(tx['version']),
                   store.intin(tx['lockTime']), tx['size']))

        # Import transaction outputs.
        tx['value_out'] = 0
        tx['value_destroyed'] = 0
        for pos in xrange(len(tx['txOut'])):
            txout = tx['txOut'][pos]
            tx['value_out'] += txout['value']
            txout_id = store.new_id("txout")

            pubkey_id = store.script_to_pubkey_id(chain, txout['scriptPubKey'])
            if pubkey_id is not None and pubkey_id <= 0:
                tx['value_destroyed'] += txout['value']

            store.sql("""
                INSERT INTO txout (
                    txout_id, tx_id, txout_pos, txout_value,
                    txout_scriptPubKey, pubkey_id
                ) VALUES (?, ?, ?, ?, ?, ?)""",
                      (txout_id, tx_id, pos, store.intin(txout['value']),
                       store.binin(txout['scriptPubKey']), pubkey_id))
            for row in store.selectall("""
                SELECT txin_id
                  FROM unlinked_txin
                 WHERE txout_tx_hash = ?
                   AND txout_pos = ?""", (dbhash, pos)):
                (txin_id,) = row
                store.sql("UPDATE txin SET txout_id = ? WHERE txin_id = ?",
                          (txout_id, txin_id))
                store.sql("DELETE FROM unlinked_txin WHERE txin_id = ?",
                          (txin_id,))
# MULTICHAIN START
            binscript = store.binout(txout['scriptPubKey'])
            script_type, data = chain.parse_txout_script(binscript)
            if pubkey_id is not None and script_type in [Chain.SCRIPT_TYPE_MULTICHAIN, Chain.SCRIPT_TYPE_MULTICHAIN_P2SH]:
                data = util.get_multichain_op_drop_data(binscript)
                if data is not None:
                    opdrop_type, val = util.parse_op_drop_data(data, chain)
                    if opdrop_type==util.OP_DROP_TYPE_ISSUE_ASSET:
                        (prefix, ) = struct.unpack("<H", dbhash[0:2])
                        new_asset_id = store.new_id("asset")
                        store.sql("""
                            INSERT INTO asset (asset_id, tx_id, chain_id, name, multiplier, issue_qty, prefix)
                            VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (new_asset_id, tx_id, chain.id, store.binin(""), 0, val, prefix ))
                        store.sql("""
                            INSERT INTO asset_address_balance (asset_id, pubkey_id, balance)
                            VALUES (?,?,?)""",
                            (new_asset_id, pubkey_id, val))
                        store.sql("""
                            INSERT INTO asset_txid (asset_id, tx_id, txout_pos)
                            VALUES (?, ?, ?)""",
                            (new_asset_id, tx_id, pos))
                        # txout['scriptPubKey'] or binscript work fine here
                        vers = chain.address_version
                        the_script_type, pubkey_hash = chain.parse_txout_script(txout['scriptPubKey'])
                        checksum = chain.address_checksum
                        if checksum is None:
                            address = util.hash_to_address(vers, pubkey_hash)
                        else:
                            address = util.hash_to_address_multichain(vers, pubkey_hash, checksum)
                        #print "New asset issued to address: {}, balance {}".format(address, val)
                    elif opdrop_type==util.OP_DROP_TYPE_SEND_ASSET or opdrop_type==util.OP_DROP_TYPE_ISSUE_MORE_ASSET:
                        msgparts = []
                        for dict in val:
                            quantity = dict['quantity']
                            assetref = dict['assetref']
                            if chain.protocol_version < 10007:
                                prefix = int( assetref.split('-')[-1] )
                            else:
                                (prefix, ) = struct.unpack("<H", binascii.unhexlify(assetref)[0:2])

                            vers = chain.address_version
                            the_script_type, pubkey_hash = chain.parse_txout_script(txout['scriptPubKey'])
                            checksum = chain.address_checksum
                            if checksum is None:
                                address = util.hash_to_address(vers, pubkey_hash)
                            else:
                                address = util.hash_to_address_multichain(vers, pubkey_hash, checksum)
                            #print "Asset sent to: {}, sent amount {}".format(address, quantity)

                            row = store.selectrow("""
                                 SELECT asset_id FROM asset WHERE asset.prefix = ?
                                 """, (prefix,))
                            if row is None:
                                break       # this should not happen!
                            asset_id = row[0]

                            store.sql("""
                            INSERT INTO asset_txid (asset_id, tx_id, txout_pos)
                            VALUES (?,?,?)""",
                            (asset_id, tx_id, pos))

                            # sqlite does not have UPSERT so get balance first before adding balance to destination address
                            row = store.selectrow("""
                                SELECT balance FROM asset_address_balance WHERE asset_id = ? AND pubkey_id = ?
                                """, (asset_id, pubkey_id))
                            if row is None:
                                balance = quantity
                                store.sql("""
                                    INSERT INTO asset_address_balance (asset_id, pubkey_id, balance)
                                    VALUES (?,?,?)""",
                                (asset_id, pubkey_id, balance))
                            else:
                                balance = row[0] + quantity
                                store.sql("""
                                    UPDATE asset_address_balance
                                       SET balance = ?
                                     WHERE pubkey_id = ? AND asset_id =?
                                     """, (balance, pubkey_id, asset_id))
                    elif opdrop_type==util.OP_DROP_TYPE_PERMISSION:
                        #print 'Permissions command detected'
                        pass
            elif pubkey_id is None and script_type is Chain.SCRIPT_TYPE_MULTICHAIN_OP_RETURN:
                opreturn_type, val = util.parse_op_return_data(data, chain)
                # Extract mandatory metadata and update asset column
                # Legacy protocol 10006
                if opreturn_type==util.OP_RETURN_TYPE_ISSUE_ASSET:
                    store.sql("""
                        UPDATE asset
                           SET name = ?, multiplier = ?
                         WHERE tx_id = ?
                         """, (unicode(val['name'], 'latin-1'), val['multiplier'], tx_id))
                    store.sql("""
                    INSERT INTO asset_txid (asset_id, tx_id, txout_pos)
                    VALUES ( (SELECT asset_id FROM asset WHERE tx_id = ? AND name = ?) , ?, ?)""",
                    (tx_id, unicode(val['name'], 'latin-1'), tx_id, pos))
            elif pubkey_id is None and script_type is Chain.SCRIPT_TYPE_MULTICHAIN_SPKN:
                # Protocol 10007
                opdrop_type, val = util.parse_op_drop_data(data, chain)
                if opdrop_type==util.OP_DROP_TYPE_SPKN_NEW_ISSUE:
                    store.sql("""
                         UPDATE asset
                            SET name = ?, multiplier = ?
                          WHERE tx_id = ?
                          """, (unicode(val.get('Asset Name',''), 'latin-1'), val.get('Quantity Multiple',1), tx_id))
                    store.sql("""
                         INSERT INTO asset_txid (asset_id, tx_id, txout_pos)
                         VALUES ( (SELECT asset_id FROM asset WHERE tx_id = ? AND name = ?) , ?, ?)""",
                         (tx_id, unicode(val.get('Asset Name',''), 'latin-1'), tx_id, pos))

# MULTICHAIN END

        # Import transaction inputs.
        tx['value_in'] = 0
        tx['unlinked_count'] = 0
        for pos in xrange(len(tx['txIn'])):
            txin = tx['txIn'][pos]
            txin_id = store.new_id("txin")

            if is_coinbase:
                txout_id = None
            else:
                txout_id, value = store.lookup_txout(
                    txin['prevout_hash'], txin['prevout_n'])
                if value is None:
                    tx['value_in'] = None
                elif tx['value_in'] is not None:
                    tx['value_in'] += value

            store.sql("""
                INSERT INTO txin (
                    txin_id, tx_id, txin_pos, txout_id""" + (""",
                    txin_scriptSig, txin_sequence""" if store.keep_scriptsig
                                                             else "") + """
                ) VALUES (?, ?, ?, ?""" + (", ?, ?" if store.keep_scriptsig
                                           else "") + """)""",
                      (txin_id, tx_id, pos, txout_id,
                       store.binin(txin['scriptSig']),
                       store.intin(txin['sequence'])) if store.keep_scriptsig
                      else (txin_id, tx_id, pos, txout_id))
            if not is_coinbase and txout_id is None:
                tx['unlinked_count'] += 1
                store.sql("""
                    INSERT INTO unlinked_txin (
                        txin_id, txout_tx_hash, txout_pos
                    ) VALUES (?, ?, ?)""",
                          (txin_id, store.hashin(txin['prevout_hash']),
                           store.intin(txin['prevout_n'])))

# MULTICHAIN START
            binscript = store.lookup_txout_scriptpubkey(txin['prevout_hash'], txin['prevout_n'])

            if txout_id is not None and binscript is not None:
                spent_tx_hash = store.hashout(txin['prevout_hash'])     # reverse out, otherwise it is backwards
                vers = chain.address_version
                the_script_type, data = chain.parse_txout_script(binscript)     # data is usually the pubkey_hash but could be dict

                if the_script_type is Chain.SCRIPT_TYPE_MULTICHAIN_ENTITY_PERMISSION:
                    pubkey_hash = data['pubkey_hash']
                else:
                    pubkey_hash = data

                if the_script_type is Chain.SCRIPT_TYPE_MULTICHAIN_P2SH:
                    vers = chain.script_addr_vers
                checksum = chain.address_checksum
                if checksum is None:
                    address = util.hash_to_address(vers, pubkey_hash)
                else:
                    address = util.hash_to_address_multichain(vers, pubkey_hash, checksum)
                pubkey_id = store.pubkey_hash_to_id(pubkey_hash, 0)

                #print "Multichain tx input = {} : {}".format(util.long_hex( spent_tx_hash ), txin['prevout_n'])

                if the_script_type in [Chain.SCRIPT_TYPE_MULTICHAIN, Chain.SCRIPT_TYPE_MULTICHAIN_P2SH]:
                    data = util.get_multichain_op_drop_data(binscript)
                    if data is not None:
                        opdrop_type, val = util.parse_op_drop_data(data, chain)
                        if opdrop_type==util.OP_DROP_TYPE_ISSUE_ASSET:
                            # Spending issue asset tx
                            #print "Issue {:d} raw units of new asset".format(val)
                            (prefix, ) = struct.unpack("<H", spent_tx_hash[0:2])
                            #print "Spending issued asset at {}, qty = {}, prefix={}".format(address, val, prefix)
                            store.sql("""
                                UPDATE asset_address_balance
                                   SET balance = balance - ?
                                 WHERE pubkey_id = ? AND
                                        asset_id = (SELECT asset_id FROM asset WHERE prefix = ?)
                                 """,
                                      (val, pubkey_id, prefix))

                            # store.sql("""
                            #     INSERT INTO asset_txid (asset_id, tx_id, txout_pos)
                            #     VALUES ((SELECT asset_id FROM asset WHERE prefix = ?),?,?)""",
                            #     (prefix, store.hashin(spent_tx_hash),  store.intin(txin['prevout_n'])))

                        elif opdrop_type in [util.OP_DROP_TYPE_SEND_ASSET, util.OP_DROP_TYPE_ISSUE_MORE_ASSET]:
                            # Spending sent tx or issue more tx
                            for dict in val:
                                quantity = dict['quantity']
                                assetref = dict['assetref']
                                if chain.protocol_version < 10007:
                                    prefix = int( assetref.split('-')[-1] )
                                else:
                                    (prefix, ) = struct.unpack("<H", binascii.unhexlify(assetref)[0:2])
                                    # If txid begins 5484... the prefix is 0x8454 in decimal.
                                    # x-y-zzzz  where zzzz = 33876

                                #print "Spending sent asset at {}, qty = {}, prefix = {} ".format(address, quantity, prefix)

                                store.sql("""
                                UPDATE asset_address_balance
                                   SET balance = balance - ?
                                 WHERE pubkey_id = ? AND
                                        asset_id = (SELECT asset_id FROM asset WHERE prefix = ?)
                                 """,
                                      (quantity, pubkey_id, prefix))

                                # store.sql("""
                                # INSERT INTO asset_txid (asset_id, tx_id, txout_pos)
                                # VALUES ((SELECT asset_id FROM asset WHERE prefix = ?),?,?)""",
                                # (prefix, store.hashin(spent_tx_hash),  store.intin(txin['prevout_n'])))

                        elif opdrop_type==util.OP_DROP_TYPE_PERMISSION:
                            #print 'Spending tx with Permissions command'
                            pass
# MULTICHAIN END

        # XXX Could populate PUBKEY.PUBKEY with txin scripts...
        # or leave that to an offline process.  Nothing in this program
        # requires them.
        return tx_id

    def import_and_commit_tx(store, tx, is_coinbase, chain):
        try:
            tx_id = store.import_tx(tx, is_coinbase, chain)
            store.commit()

        except store.dbmodule.DatabaseError:
            store.rollback()
            # Violation of tx_hash uniqueness?
            tx_id = store.tx_find_id_and_value(tx, is_coinbase)
            if not tx_id:
                raise

        return tx_id

    def maybe_import_binary_tx(store, chain_name, binary_tx):
        if chain_name is None:
            chain = store.get_default_chain()
        else:
            chain = store.get_chain_by_name(chain_name)

        tx_hash = chain.transaction_hash(binary_tx)

        (count,) = store.selectrow(
            "SELECT COUNT(1) FROM tx WHERE tx_hash = ?",
            (store.hashin(tx_hash),))

        if count == 0:
            tx = chain.parse_transaction(binary_tx)
            tx['hash'] = tx_hash
            store.import_tx(tx, chain.is_coinbase_tx(tx), chain)
            store.imported_bytes(tx['size'])

    def export_tx(store, tx_id=None, tx_hash=None, decimals=8, format="api", chain=None):
        """Return a dict as seen by /rawtx or None if not found."""

        # TODO: merge _export_tx_detail with export_tx.
        if format == 'browser':
            return store._export_tx_detail(tx_hash, chain=chain)

        tx = {}
        is_bin = format == "binary"

        if tx_id is not None:
            row = store.selectrow("""
                SELECT tx_hash, tx_version, tx_lockTime, tx_size
                  FROM tx
                 WHERE tx_id = ?
            """, (tx_id,))
            if row is None:
                return None
            tx['hash'] = store.hashout_hex(row[0])

        elif tx_hash is not None:
            row = store.selectrow("""
                SELECT tx_id, tx_version, tx_lockTime, tx_size
                  FROM tx
                 WHERE tx_hash = ?
            """, (store.hashin_hex(tx_hash),))
            if row is None:
                return None
            tx['hash'] = tx_hash.decode('hex')[::-1] if is_bin else tx_hash
            tx_id = row[0]

        else:
            raise ValueError("export_tx requires either tx_id or tx_hash.")

        tx['version' if is_bin else 'ver']        = int(row[1])
        tx['lockTime' if is_bin else 'lock_time'] = int(row[2])
        tx['size'] = int(row[3])

        txins = []
        tx['txIn' if is_bin else 'in'] = txins
        for row in store.selectall("""
            SELECT
                COALESCE(tx.tx_hash, uti.txout_tx_hash),
                COALESCE(txout.txout_pos, uti.txout_pos)""" + (""",
                txin_scriptSig,
                txin_sequence""" if store.keep_scriptsig else "") + """
            FROM txin
            LEFT JOIN txout ON (txin.txout_id = txout.txout_id)
            LEFT JOIN tx ON (txout.tx_id = tx.tx_id)
            LEFT JOIN unlinked_txin uti ON (txin.txin_id = uti.txin_id)
            WHERE txin.tx_id = ?
            ORDER BY txin.txin_pos""", (tx_id,)):
            prevout_hash = row[0]
            prevout_n = None if row[1] is None else int(row[1])
            if is_bin:
                txin = {
                    'prevout_hash': store.hashout(prevout_hash),
                    'prevout_n': prevout_n}
            else:
                if prevout_hash is None:
                    prev_out = {
                        'hash': "0" * 64,  # XXX should store this?
                        'n': 0xffffffff}   # XXX should store this?
                else:
                    prev_out = {
                        'hash': store.hashout_hex(prevout_hash),
                        'n': prevout_n}
                txin = {'prev_out': prev_out}
            if store.keep_scriptsig:
                scriptSig = row[2]
                sequence = row[3]
                if is_bin:
                    txin['scriptSig'] = store.binout(scriptSig)
                else:
                    txin['raw_scriptSig'] = store.binout_hex(scriptSig)
                txin['sequence'] = None if sequence is None else int(sequence)
            txins.append(txin)

        txouts = []
        tx['txOut' if is_bin else 'out'] = txouts
        for satoshis, scriptPubKey in store.selectall("""
            SELECT txout_value, txout_scriptPubKey
              FROM txout
             WHERE tx_id = ?
            ORDER BY txout_pos""", (tx_id,)):

            if is_bin:
                txout = {
                    'value': int(satoshis),
                    'scriptPubKey': store.binout(scriptPubKey)}
            else:
                coin = 10 ** decimals
                satoshis = int(satoshis)
                integer = satoshis / coin
                frac = satoshis % coin
                txout = {
                    'value': ("%%d.%%0%dd" % (decimals,)) % (integer, frac),
                    'raw_scriptPubKey': store.binout_hex(scriptPubKey)}
            txouts.append(txout)

        if not is_bin:
            tx['vin_sz'] = len(txins)
            tx['vout_sz'] = len(txouts)

        return tx

    def _export_tx_detail(store, tx_hash, chain):
        try:
            dbhash = store.hashin_hex(tx_hash)
        except TypeError:
            raise MalformedHash()

        row = store.selectrow("""
            SELECT tx_id, tx_version, tx_lockTime, tx_size
              FROM tx
             WHERE tx_hash = ?
        """, (dbhash,))
        if row is None:
            return None

        tx_id = int(row[0])
        tx = {
            'hash': tx_hash,
            'version': int(row[1]),
            'lockTime': int(row[2]),
            'size': int(row[3]),
            }

        def parse_tx_cc(row):
            return {
                'chain': store.get_chain_by_id(row[0]),
                'in_longest': int(row[1]),
                'block_nTime': int(row[2]),
                'block_height': None if row[3] is None else int(row[3]),
                'block_hash': store.hashout_hex(row[4]),
                'tx_pos': int(row[5])
                }

        tx['chain_candidates'] = map(parse_tx_cc, store.selectall("""
            SELECT cc.chain_id, cc.in_longest,
                   b.block_nTime, b.block_height, b.block_hash,
                   block_tx.tx_pos
              FROM chain_candidate cc
              JOIN block b ON (b.block_id = cc.block_id)
              JOIN block_tx ON (block_tx.block_id = b.block_id)
             WHERE block_tx.tx_id = ?
             ORDER BY cc.chain_id, cc.in_longest DESC, b.block_hash
        """, (tx_id,)))

        if chain is None:
            if len(tx['chain_candidates']) > 0:
                chain = tx['chain_candidates'][0]['chain']
            else:
                chain = store.get_default_chain()

        def parse_row(row):
            pos, script, value, o_hash, o_pos = row[:5]
            script = store.binout(script)
            scriptPubKey = store.binout(row[5]) if len(row) >5 else script

            ret = {
                "pos": int(pos),
                "binscript": script,
                "value": None if value is None else int(value),
                "o_hash": store.hashout_hex(o_hash),
                "o_pos": None if o_pos is None else int(o_pos),
                }
            store._export_scriptPubKey(ret, chain, scriptPubKey)
# MULTICHAIN START
            ret['multichain_scriptPubKey'] = scriptPubKey if len(row) > 5 else None
# MULTICHAIN END
            return ret

        # XXX Unneeded outer join.
        tx['in'] = map(parse_row, store.selectall("""
            SELECT
                txin.txin_pos""" + (""",
                txin.txin_scriptSig""" if store.keep_scriptsig else """,
                NULL""") + """,
                txout.txout_value,
                COALESCE(prevtx.tx_hash, u.txout_tx_hash),
                COALESCE(txout.txout_pos, u.txout_pos),
                txout.txout_scriptPubKey
              FROM txin
              LEFT JOIN txout ON (txout.txout_id = txin.txout_id)
              LEFT JOIN tx prevtx ON (txout.tx_id = prevtx.tx_id)
              LEFT JOIN unlinked_txin u ON (u.txin_id = txin.txin_id)
             WHERE txin.tx_id = ?
             ORDER BY txin.txin_pos
        """, (tx_id,)))

        # XXX Only one outer join needed.
        tx['out'] = map(parse_row, store.selectall("""
            SELECT
                txout.txout_pos,
                txout.txout_scriptPubKey,
                txout.txout_value,
                nexttx.tx_hash,
                txin.txin_pos
              FROM txout
              LEFT JOIN txin ON (txin.txout_id = txout.txout_id)
              LEFT JOIN tx nexttx ON (txin.tx_id = nexttx.tx_id)
             WHERE txout.tx_id = ?
             ORDER BY txout.txout_pos
        """, (tx_id,)))

        def sum_values(rows):
            ret = 0
            for row in rows:
                if row['value'] is None:
                    return None
                ret += row['value']
            return ret

        tx['value_in'] = sum_values(tx['in'])
        tx['value_out'] = sum_values(tx['out'])

        return tx

    def export_address_history(store, address, chain=None, max_rows=-1, types=frozenset(['direct', 'escrow'])):
        version, binaddr = util.decode_check_address_multichain(address)
        if binaddr is None:
            raise MalformedAddress("Invalid address")

        balance = {}
        received = {}
        sent = {}
        counts = [0, 0]
        chains = []

        def adj_balance(txpoint):
            chain = txpoint['chain']

            if chain.id not in balance:
                chains.append(chain)
                balance[chain.id] = 0
                received[chain.id] = 0
                sent[chain.id] = 0

            if txpoint['type'] == 'direct':
                value = txpoint['value']
                balance[chain.id] += value
                if txpoint['is_out']:
                    sent[chain.id] -= value
                else:
                    received[chain.id] += value
                counts[txpoint['is_out']] += 1

        dbhash = store.binin(binaddr)
        txpoints = []

        def parse_row(is_out, row_type, nTime, chain_id, height, blk_hash, tx_hash, pos, value, script=None):
            chain = store.get_chain_by_id(chain_id)
            txpoint = {
                'type':     row_type,
                'is_out':   int(is_out),
                'nTime':    int(nTime),
                'chain':    chain,
                'height':   int(height),
                'blk_hash': store.hashout_hex(blk_hash),
                'tx_hash':  store.hashout_hex(tx_hash),
                'pos':      int(pos),
                'value':    int(value),
                }
            if script is not None:
                store._export_scriptPubKey(txpoint, chain, store.binout(script))

            return txpoint

        def parse_direct_in(row):  return parse_row(True, 'direct', *row)
        def parse_direct_out(row): return parse_row(False, 'direct', *row)
        def parse_escrow_in(row):  return parse_row(True, 'escrow', *row)
        def parse_escrow_out(row): return parse_row(False, 'escrow', *row)

        def get_received(escrow):
            return store.selectall("""
                SELECT
                    b.block_nTime,
                    cc.chain_id,
                    b.block_height,
                    b.block_hash,
                    tx.tx_hash,
                    txin.txin_pos,
                    -prevout.txout_value""" + (""",
                    prevout.txout_scriptPubKey""" if escrow else "") + """
                  FROM chain_candidate cc
                  JOIN block b ON (b.block_id = cc.block_id)
                  JOIN block_tx ON (block_tx.block_id = b.block_id)
                  JOIN tx ON (tx.tx_id = block_tx.tx_id)
                  JOIN txin ON (txin.tx_id = tx.tx_id)
                  JOIN txout prevout ON (txin.txout_id = prevout.txout_id)""" + ("""
                  JOIN multisig_pubkey mp ON (mp.multisig_id = prevout.pubkey_id)""" if escrow else "") + """
                  JOIN pubkey ON (pubkey.pubkey_id = """ + ("mp" if escrow else "prevout") + """.pubkey_id)
                 WHERE pubkey.pubkey_hash = ?
                   AND cc.in_longest = 1""" + ("" if max_rows < 0 else """
                 LIMIT ?"""),
                          (dbhash,)
                          if max_rows < 0 else
                          (dbhash, max_rows + 1))

        def get_sent(escrow):
            return store.selectall("""
                SELECT
                    b.block_nTime,
                    cc.chain_id,
                    b.block_height,
                    b.block_hash,
                    tx.tx_hash,
                    txout.txout_pos,
                    txout.txout_value""" + (""",
                    txout.txout_scriptPubKey""" if escrow else "") + """
                  FROM chain_candidate cc
                  JOIN block b ON (b.block_id = cc.block_id)
                  JOIN block_tx ON (block_tx.block_id = b.block_id)
                  JOIN tx ON (tx.tx_id = block_tx.tx_id)
                  JOIN txout ON (txout.tx_id = tx.tx_id)""" + ("""
                  JOIN multisig_pubkey mp ON (mp.multisig_id = txout.pubkey_id)""" if escrow else "") + """
                  JOIN pubkey ON (pubkey.pubkey_id = """ + ("mp" if escrow else "txout") + """.pubkey_id)
                 WHERE pubkey.pubkey_hash = ?
                   AND cc.in_longest = 1""" + ("" if max_rows < 0 else """
                 LIMIT ?"""),
                          (dbhash, max_rows + 1)
                          if max_rows >= 0 else
                          (dbhash,))

        if 'direct' in types:
            in_rows = get_received(False)
            if len(in_rows) > max_rows >= 0:
                return None  # XXX Could still show address basic data.
            txpoints += map(parse_direct_in, in_rows)

            out_rows = get_sent(False)
            if len(out_rows) > max_rows >= 0:
                return None
            txpoints += map(parse_direct_out, out_rows)

        if 'escrow' in types:
            in_rows = get_received(True)
            if len(in_rows) > max_rows >= 0:
                return None
            txpoints += map(parse_escrow_in, in_rows)

            out_rows = get_sent(True)
            if len(out_rows) > max_rows >= 0:
                return None
            txpoints += map(parse_escrow_out, out_rows)

        def cmp_txpoint(p1, p2):
            return cmp(p1['nTime'], p2['nTime']) \
                or cmp(p1['is_out'], p2['is_out']) \
                or cmp(p1['height'], p2['height']) \
                or cmp(p1['chain'].name, p2['chain'].name)

        txpoints.sort(cmp_txpoint)

        for txpoint in txpoints:
            adj_balance(txpoint)

        hist = {
            'binaddr':  binaddr,
            'version':  version,
            'chains':   chains,
            'txpoints': txpoints,
            'balance':  balance,
            'sent':     sent,
            'received': received,
            'counts':   counts
            }

        # Show P2SH address components, if known.
        # XXX With some more work, we could find required_signatures.
        for (subbinaddr,) in store.selectall("""
            SELECT sub.pubkey_hash
              FROM multisig_pubkey mp
              JOIN pubkey top ON (mp.multisig_id = top.pubkey_id)
              JOIN pubkey sub ON (mp.pubkey_id = sub.pubkey_id)
             WHERE top.pubkey_hash = ?""", (dbhash,)):
            if 'subbinaddr' not in hist:
                hist['subbinaddr'] = []
            hist['subbinaddr'].append(store.binout(subbinaddr))

        return hist

    # Called to indicate that the given block has the correct magic
    # number and policy for the given chains.  Updates CHAIN_CANDIDATE
    # and CHAIN.CHAIN_LAST_BLOCK_ID as appropriate.
    def offer_block_to_chains(store, b, chain_ids):
        b['top'] = store.adopt_orphans(b, 0, chain_ids, chain_ids)
        for chain_id in chain_ids:
            store._offer_block_to_chain(b, chain_id)

    def _offer_block_to_chain(store, b, chain_id):
        if b['chain_work'] is None:
            in_longest = 0
        else:
            # Do we produce a chain longer than the current chain?
            # Query whether the new block (or its tallest descendant)
            # beats the current chain_last_block_id.  Also check
            # whether the current best is our top, which indicates
            # this block is in longest; this can happen in database
            # repair scenarios.
            top = b['top'][chain_id][0]
            row = store.selectrow("""
                SELECT b.block_id, b.block_height, b.block_chain_work
                  FROM block b, chain c
                 WHERE c.chain_id = ?
                   AND b.block_id = c.chain_last_block_id""", (chain_id,))
            if row:
                loser_id, loser_height, loser_work = row
                if loser_id != top['block_id'] and \
                        store.binout_int(loser_work) >= top['chain_work']:
                    row = None
            if row:
                # New longest chain.
                in_longest = 1
                to_connect = []
                to_disconnect = []
                winner_id = top['block_id']
                winner_height = top['height']
                while loser_height > winner_height:
                    to_disconnect.insert(0, loser_id)
                    loser_id = store.get_prev_block_id(loser_id)
                    loser_height -= 1
                while winner_height > loser_height:
                    to_connect.insert(0, winner_id)
                    winner_id = store.get_prev_block_id(winner_id)
                    winner_height -= 1
                loser_height = None
                while loser_id != winner_id:
                    to_disconnect.insert(0, loser_id)
                    loser_id = store.get_prev_block_id(loser_id)
                    to_connect.insert(0, winner_id)
                    winner_id = store.get_prev_block_id(winner_id)
                    winner_height -= 1
                for block_id in to_disconnect:
                    store.disconnect_block(block_id, chain_id)
                for block_id in to_connect:
                    store.connect_block(block_id, chain_id)

            elif b['hashPrev'] == store.get_chain_by_id(chain_id).genesis_hash_prev:
                in_longest = 1  # Assume only one genesis block per chain.  XXX
            else:
                in_longest = 0

        store.sql("""
            INSERT INTO chain_candidate (
                chain_id, block_id, in_longest, block_height
            ) VALUES (?, ?, ?, ?)""",
                  (chain_id, b['block_id'], in_longest, b['height']))

        if in_longest > 0:
            store.sql("""
                UPDATE chain
                   SET chain_last_block_id = ?
                 WHERE chain_id = ?""", (top['block_id'], chain_id))

        if store.use_firstbits and b['height'] is not None:
            (addr_vers,) = store.selectrow("""
                SELECT chain_address_version
                  FROM chain
                 WHERE chain_id = ?""", (chain_id,))
            store.do_vers_firstbits(addr_vers, b['block_id'])

    def offer_existing_block(store, hash, chain_id):
        block_row = store.selectrow("""
            SELECT block_id, block_height, block_chain_work,
                   block_nTime, block_total_seconds,
                   block_total_satoshis, block_satoshi_seconds,
                   block_total_ss
              FROM block
             WHERE block_hash = ?
        """, (store.hashin(hash),))

        if not block_row:
            return False

        if chain_id is None:
            return True

        # Block header already seen.  Don't import the block,
        # but try to add it to the chain.

        b = {
            "block_id":   block_row[0],
            "height":     block_row[1],
            "chain_work": store.binout_int(block_row[2]),
            "nTime":      block_row[3],
            "seconds":    block_row[4],
            "satoshis":   block_row[5],
            "ss":         block_row[6],
            "total_ss":   block_row[7]}

        if store.selectrow("""
            SELECT 1
              FROM chain_candidate
             WHERE block_id = ?
               AND chain_id = ?""",
                        (b['block_id'], chain_id)):
            store.log.info("block %d already in chain %d",
                           b['block_id'], chain_id)
        else:
            if b['height'] == 0:
                b['hashPrev'] = store.get_chain_by_id(chain_id).genesis_hash_prev
            else:
                b['hashPrev'] = 'dummy'  # Fool adopt_orphans.
            store.offer_block_to_chains(b, frozenset([chain_id]))

        return True

    def find_next_blocks(store, block_id):
        ret = []
        for row in store.selectall(
            "SELECT next_block_id FROM block_next WHERE block_id = ?",
            (block_id,)):
            ret.append(row[0])
        return ret

    def find_chains_containing_block(store, block_id):
        ret = []
        for row in store.selectall(
            "SELECT chain_id FROM chain_candidate WHERE block_id = ?",
            (block_id,)):
            ret.append(row[0])
        return frozenset(ret)

    def get_prev_block_id(store, block_id):
        return store.selectrow(
            "SELECT prev_block_id FROM block WHERE block_id = ?",
            (block_id,))[0]

    def disconnect_block(store, block_id, chain_id):
        store.sql("""
            UPDATE chain_candidate
               SET in_longest = 0
             WHERE block_id = ? AND chain_id = ?""",
                  (block_id, chain_id))

    def connect_block(store, block_id, chain_id):
        store.sql("""
            UPDATE chain_candidate
               SET in_longest = 1
             WHERE block_id = ? AND chain_id = ?""",
                  (block_id, chain_id))

    def lookup_txout(store, tx_hash, txout_pos):
        row = store.selectrow("""
            SELECT txout.txout_id, txout.txout_value
              FROM txout, tx
             WHERE txout.tx_id = tx.tx_id
               AND tx.tx_hash = ?
               AND txout.txout_pos = ?""",
                  (store.hashin(tx_hash), txout_pos))

    def lookup_txout_scriptpubkey(store, tx_hash, txout_pos):
        row = store.selectrow("""
            SELECT txout_scriptPubKey
              FROM txout, tx
             WHERE txout.tx_id = tx.tx_id
               AND tx.tx_hash = ?
               AND txout.txout_pos = ?""",
                  (store.hashin(tx_hash), txout_pos))

    def script_to_pubkey_id(store, chain, script):
        """Extract address and script type from transaction output script."""
        script_type, data = chain.parse_txout_script(script)

        if script_type in (Chain.SCRIPT_TYPE_ADDRESS, Chain.SCRIPT_TYPE_P2SH):
            return store.pubkey_hash_to_id(data)

        if script_type == Chain.SCRIPT_TYPE_MULTICHAIN_P2SH:
            return store.pubkey_hash_to_id(data, PUBKEY_FLAGS_P2SH)

        if script_type == Chain.SCRIPT_TYPE_MULTICHAIN:
            return store.pubkey_hash_to_id(data)

        if script_type == Chain.SCRIPT_TYPE_MULTICHAIN_ENTITY_PERMISSION:
            return store.pubkey_hash_to_id(data['pubkey_hash'])

        if script_type == Chain.SCRIPT_TYPE_PUBKEY:
            return store.pubkey_to_id(chain, data)

        if script_type == Chain.SCRIPT_TYPE_MULTISIG:
            script_hash = chain.script_hash(script)
            multisig_id = store._pubkey_id(script_hash, script)

            if not store.selectrow("SELECT 1 FROM multisig_pubkey WHERE multisig_id = ?", (multisig_id,)):
                for pubkey in set(data['pubkeys']):
                    pubkey_id = store.pubkey_to_id(chain, pubkey)
                    store.sql("""
                        INSERT INTO multisig_pubkey (multisig_id, pubkey_id)
                        VALUES (?, ?)""", (multisig_id, pubkey_id))
            return multisig_id

        if script_type == Chain.SCRIPT_TYPE_BURN:
            return PUBKEY_ID_NETWORK_FEE

        return None

    def pubkey_hash_to_id(store, pubkey_hash, flags=0):
        return store._pubkey_id(pubkey_hash, None, flags)

    def pubkey_to_id(store, chain, pubkey, flags=0):
        pubkey_hash = chain.pubkey_hash(pubkey)
        return store._pubkey_id(pubkey_hash, pubkey, flags)

    def _pubkey_id(store, pubkey_hash, pubkey, flags=0):
        dbhash = store.binin(pubkey_hash)  # binin, not hashin for 160-bit
        row = store.selectrow("""
            SELECT pubkey_id
              FROM pubkey
             WHERE pubkey_hash = ?""", (dbhash,))
        if row:
            return row[0]
        pubkey_id = store.new_id("pubkey")

        if pubkey is not None and len(pubkey) > MAX_PUBKEY:
            pubkey = None

        store.sql("""
            INSERT INTO pubkey (pubkey_id, pubkey_hash, pubkey, pubkey_flags)
            VALUES (?, ?, ?, ?)""",
                  (pubkey_id, dbhash, store.binin(pubkey), flags ))
        return pubkey_id

    def flush(store):
        if store.bytes_since_commit > 0:
            store.commit()
            store.log.debug("commit")
            store.bytes_since_commit = 0

    def imported_bytes(store, size):
        store.bytes_since_commit += size
        if store.bytes_since_commit >= store.commit_bytes:
            store.flush()

    def catch_up(store):
        for dircfg in store.datadirs:
            try:
                loader = dircfg['loader'] or store.default_loader
                if loader == "blkfile":
                    store.catch_up_dir(dircfg)
                elif loader in ("rpc", "rpc,blkfile", "default"):
                    if not store.catch_up_rpc(dircfg):
                        if loader == "rpc":
                            raise Exception("RPC load failed")
                        store.log.debug("catch_up_rpc: abort")
                        store.catch_up_dir(dircfg)

    def catch_up_rpc(store, dircfg):
        """
        Load new blocks using RPC.  Requires running *coind supporting
        getblockhash, getblock, and getrawtransaction.  Bitcoind v0.8
        requires the txindex configuration option.  Requires chain_id
        in the datadir table.
        """

        # Expand ~ in multichain folder to user home directory
        dircfg['dirname'] = os.path.expanduser(dircfg['dirname'])
        # Extract chain name from last path component of multichain folder
        chain_name = os.path.basename(dircfg['dirname'])

        chain_id = dircfg['chain_id']
        if chain_id is None:
            store.log.error("no chain_id")
            return False
        chain = store.chains_by.id[chain_id]

        conffile = dircfg.get('conf') or chain.datadir_conf_file_name
        conffile = os.path.join(dircfg['dirname'], conffile)
        try:
            conf = dict([line.strip().split("=", 1)
                         if "=" in line
                         else (line.strip(), True)
                         for line in open(conffile)
                         if line != "" and line[0] not in "#\r\n"])
        except Exception, e:
            store.log.error("failed to load %s: %s", conffile, e)
            return False

        rpcuser     = conf.get("rpcuser", "")
        rpcpassword = conf["rpcpassword"]
        rpcconnect  = conf.get("rpcconnect", "127.0.0.1")
        rpcport     = conf.get("rpcport", chain.datadir_rpcport)
        url = "http://" + rpcuser + ":" + rpcpassword + "@" + rpcconnect \
            + ":" + str(rpcport)

        def rpc(func, *params):
            store.rpclog.info("RPC>> %s %s %s", chain_name, func, params)
            ret = util.jsonrpc(chain_name, url, func, *params)

            if (store.rpclog.isEnabledFor(logging.INFO)):
                store.rpclog.info("RPC<< %s",
                                  re.sub(r'\[[^\]]{100,}\]', '[...]', str(ret)))
            return ret

        def get_blockhash(height):
            try:
                return rpc("getblockhash", height)


        # Returns -1 on error, so we'll get 0 on empty chain
        height = store.get_block_number(chain.id) + 1

        def get_tx(rpc_tx_hash):
            try:
                rpc_tx_hex = rpc("getrawtransaction", rpc_tx_hash)

            except util.JsonrpcException, e:
                if e.code != -5 and e.code!= -710:  # -5 or -710: transaction not in index.
                    raise
                if height != 0:
                    return None

                # The genesis transaction is unavailable.  This is
                # normal.
                import genesis_tx
                rpc_tx_hex = genesis_tx.get(rpc_tx_hash)
                if rpc_tx_hex is None:
                    store.log.error("genesis transaction unavailable via RPC;"
                                    " see import-tx in abe.conf")
                    return None

            rpc_tx = rpc_tx_hex.decode('hex')
            tx_hash = rpc_tx_hash.decode('hex')[::-1]

            computed_tx_hash = chain.transaction_hash(rpc_tx)
            if tx_hash != computed_tx_hash:
                #raise InvalidBlock('transaction hash mismatch')
                store.log.debug('transaction hash mismatch: %r != %r', tx_hash, computed_tx_hash)

            tx = chain.parse_transaction(rpc_tx)
            tx['hash'] = tx_hash
            return tx

        def first_new_block(height, next_hash):
            """Find the first new block."""

            while height > 0:
                hash = get_blockhash(height - 1)

                if hash is not None and (1,) == store.selectrow("""
                    SELECT 1
                      FROM chain_candidate cc
                      JOIN block b ON (cc.block_id = b.block_id)
                     WHERE b.block_hash = ?
                       AND b.block_height IS NOT NULL
                       AND cc.chain_id = ?""", (
                        store.hashin_hex(str(hash)), chain.id)):
                    break

                next_hash = hash
                height -= 1

            return (height, next_hash)

        def catch_up_mempool(height):
            # imported tx cache, so we can avoid querying DB on each pass
            imported_tx = set()
            # Next height check time
            height_chk = time.time() + 1

            while store.rpc_load_mempool:
                # Import the memory pool.
                for rpc_tx_hash in rpc("getrawmempool"):
                    if rpc_tx_hash in imported_tx: continue

                    # Break loop if new block found
                    if height_chk < time.time():
                        rpc_hash = get_blockhash(height)
                        if rpc_hash:
                            return rpc_hash
                        height_chk = time.time() + 1

                    tx = get_tx(rpc_tx_hash)
                    if tx is None:
                        # NB: On new blocks, older mempool tx are often missing
                        # This happens some other times too, just get over with
                        store.log.info("tx %s gone from mempool" % rpc_tx_hash)
                        continue

                    # XXX Race condition in low isolation levels.
                    tx_id = store.tx_find_id_and_value(tx, False, check_only=True)
                    if tx_id is None:
                        tx_id = store.import_tx(tx, False, chain)
                        store.log.info("mempool tx %d", tx_id)
                        store.imported_bytes(tx['size'])
                    imported_tx.add(rpc_tx_hash)

                store.log.info("mempool load completed, starting over...")
                time.sleep(3)
            return None

        try:

            # Get block hash at height, and at the same time, test
            # bitcoind connectivity.
            try:
                next_hash = get_blockhash(height)
            except util.JsonrpcException, e:
                raise
            except Exception, e:
                # Connectivity failure.
                store.log.error("RPC failed: %s", e)
                return False

            # Get the first new block (looking backward until hash match)
            height, next_hash = first_new_block(height, next_hash)

            # Import new blocks.
            rpc_hash = next_hash or get_blockhash(height)
            if rpc_hash is None:
                rpc_hash = catch_up_mempool(height)
            while rpc_hash is not None:
                hash = rpc_hash.decode('hex')[::-1]

                if store.offer_existing_block(hash, chain.id):
                    rpc_hash = get_blockhash(height + 1)
                else:
                    rpc_block = rpc("getblock", rpc_hash)
                    assert rpc_hash == rpc_block['hash']

                    prev_hash = \
                        rpc_block['previousblockhash'].decode('hex')[::-1] \
                        if 'previousblockhash' in rpc_block \
                        else chain.genesis_hash_prev

                    block = {
                        'hash':     hash,
                        'version':  int(rpc_block['version']),
                        'hashPrev': prev_hash,
                        'hashMerkleRoot':
                            rpc_block['merkleroot'].decode('hex')[::-1],
                        'nTime':    int(rpc_block['time']),
                        'nBits':    int(rpc_block['bits'], 16),
                        'nNonce':   int(rpc_block['nonce']),
                        'transactions': [],
                        'size':     int(rpc_block['size']),
                        'height':   height,
                        }

                    if chain.block_header_hash(chain.serialize_block_header(
                            block)) != hash:
                        raise InvalidBlock('block hash mismatch')

                    for rpc_tx_hash in rpc_block['tx']:
                        tx = store.export_tx(tx_hash = str(rpc_tx_hash),
                                             format = "binary")
                        if tx is None:
                            tx = get_tx(rpc_tx_hash)
                            if tx is None:
                                store.log.error("RPC service lacks full txindex")
                                return False

                        block['transactions'].append(tx)

                    store.import_block(block, chain = chain)
                    store.imported_bytes(block['size'])
                    rpc_hash = rpc_block.get('nextblockhash')

                height += 1
                if rpc_hash is None:
                    rpc_hash = catch_up_mempool(height)
                    # Also look backwards in case we end up on an orphan block.
                    # NB: Call only when rpc_hash is not None, otherwise
                    #     we'll override catch_up_mempool's behavior.
                    if rpc_hash:
                        height, rpc_hash = first_new_block(height, rpc_hash)

        except util.JsonrpcMethodNotFound, e:
            store.log.error("bitcoind %s not supported", e.method)
            return False

        except InvalidBlock, e:
            store.log.error("RPC data not understood: %s", e)
            return False

        return True

    # Load all blocks starting at the current file and offset.
    def catch_up_dir(store, dircfg):
        def open_blkfile(number):
            store._refresh_dircfg(dircfg)
            blkfile = {
                'stream': BCDataStream.BCDataStream(),
                'name': store.blkfile_name(dircfg, number),
                'number': number
                }

            try:
                file = open(blkfile['name'], "rb")
            except IOError, e:
                # Early bitcoind used blk0001.dat to blk9999.dat.
                # Now it uses blocks/blk00000.dat to blocks/blk99999.dat.
                # Abe starts by assuming the former scheme.  If we don't
                # find the expected file but do see blocks/blk00000.dat,
                # switch to the new scheme.  Record the switch by adding
                # 100000 to each file number, so for example, 100123 means
                # blocks/blk00123.dat but 123 still means blk0123.dat.
                if blkfile['number'] > 9999 or e.errno != errno.ENOENT:
                    raise
                new_number = 100000
                blkfile['name'] = store.blkfile_name(dircfg, new_number)
                file = open(blkfile['name'], "rb")
                blkfile['number'] = new_number

            try:
                blkfile['stream'].map_file(file, 0)
            except Exception:
                # mmap can fail on an empty file, but empty files are okay.
                file.seek(0, os.SEEK_END)
                if file.tell() == 0:
                    blkfile['stream'].input = ""
                    blkfile['stream'].read_cursor = 0
                else:
                    blkfile['stream'].map_file(file, 0)
            finally:
                file.close()
            store.log.info("Opened %s", blkfile['name'])
            return blkfile

        def try_close_file(ds):
            try:
                ds.close_file()
            except Exception, e:
                store.log.info("BCDataStream: close_file: %s", e)

        try:
            blkfile = open_blkfile(dircfg['blkfile_number'])
        except IOError, e:
            store.log.warning("Skipping datadir %s: %s", dircfg['dirname'], e)
            return

        while True:
            dircfg['blkfile_number'] = blkfile['number']
            ds = blkfile['stream']
            next_blkfile = None

            try:
                store.import_blkdat(dircfg, ds, blkfile['name'])
            except Exception:
                store.log.warning("Exception at %d" % ds.read_cursor)
                try_close_file(ds)
                raise

            if next_blkfile is None:
                # Try another file.
                try:
                    next_blkfile = open_blkfile(dircfg['blkfile_number'] + 1)
                except IOError, e:
                    if e.errno != errno.ENOENT:
                        raise
                    # No more block files.
                    return
                except Exception, e:
                    if getattr(e, 'errno', None) == errno.ENOMEM:
                        # Assume 32-bit address space exhaustion.
                        store.log.warning(
                            "Cannot allocate memory for next blockfile: "
                            "skipping safety check")
                        try_close_file(ds)
                        blkfile = open_blkfile(dircfg['blkfile_number'] + 1)
                        dircfg['blkfile_offset'] = 0
                        continue
                    raise
                finally:
                    if next_blkfile is None:
                        try_close_file(ds)

                # Load any data written to the last file since we checked.
                store.import_blkdat(dircfg, ds, blkfile['name'])

                # Continue with the new file.
                blkfile = next_blkfile

            try_close_file(ds)
            dircfg['blkfile_offset'] = 0

    # Load all blocks from the given data stream.
    def import_blkdat(store, dircfg, ds, filename="[unknown]"):
        filenum = dircfg['blkfile_number']
        ds.read_cursor = dircfg['blkfile_offset']

        while filenum == dircfg['blkfile_number']:
            if ds.read_cursor + 8 > len(ds.input):
                break

            offset = ds.read_cursor
            magic = ds.read_bytes(4)

            # Assume no real magic number starts with a NUL.
            if magic[0] == "\0":
                if filenum > 99999 and magic == "\0\0\0\0":
                    # As of Bitcoin 0.8, files often end with a NUL span.
                    ds.read_cursor = offset
                    break
                # Skip NUL bytes at block end.
                ds.read_cursor = offset
                while ds.read_cursor < len(ds.input):
                    size = min(len(ds.input) - ds.read_cursor, 1000)
                    data = ds.read_bytes(size).lstrip("\0")
                    if (data != ""):
                        ds.read_cursor -= len(data)
                        break
                store.log.info("Skipped %d NUL bytes at block end",
                               ds.read_cursor - offset)
                continue

            # Assume blocks obey the respective policy if they get here.
            chain_id = dircfg['chain_id']
            chain = store.chains_by.id.get(chain_id, None)

            if chain is None:
                chain = store.chains_by.magic.get(magic, None)

            if chain is None:
                store.log.warning(
                    "Chain not found for magic number %s in block file %s at"
                    " offset %d.", magic.encode('hex'), filename, offset)

                not_magic = magic
                # Read this file's initial magic number.
                magic = ds.input[0:4]

                if magic == not_magic:
                    ds.read_cursor = offset
                    break

                store.log.info(
                    "Scanning for initial magic number %s.",
                    magic.encode('hex'))

                ds.read_cursor = offset
                offset = ds.input.find(magic, offset)
                if offset == -1:
                    store.log.info("Magic number scan unsuccessful.")
                    break

                store.log.info(
                    "Skipped %d bytes in block file %s at offset %d.",
                    offset - ds.read_cursor, filename, ds.read_cursor)

                ds.read_cursor = offset
                continue

            length = ds.read_int32()
            if ds.read_cursor + length > len(ds.input):
                store.log.debug("incomplete block of length %d chain %d",
                                length, chain.id)
                ds.read_cursor = offset
                break
            end = ds.read_cursor + length

            hash = chain.ds_block_header_hash(ds)

            # XXX should decode target and check hash against it to
            # avoid loading garbage data.  But not for merged-mined or
            # CPU-mined chains that use different proof-of-work
            # algorithms.

            if not store.offer_existing_block(hash, chain.id):
                b = chain.ds_parse_block(ds)
                b["hash"] = hash

                if (store.log.isEnabledFor(logging.DEBUG) and b["hashPrev"] == chain.genesis_hash_prev):
                    try:
                        store.log.debug("Chain %d genesis tx: %s", chain.id,
                                        b['transactions'][0]['__data__'].encode('hex'))
                    except Exception:
                        pass

                store.import_block(b, chain = chain)
                if ds.read_cursor != end:
                    store.log.debug("Skipped %d bytes at block end",
                                    end - ds.read_cursor)

            ds.read_cursor = end

            store.bytes_since_commit += length
            if store.bytes_since_commit >= store.commit_bytes:
                store.save_blkfile_offset(dircfg, ds.read_cursor)
                store.flush()
                store._refresh_dircfg(dircfg)

        if ds.read_cursor != dircfg['blkfile_offset']:
            store.save_blkfile_offset(dircfg, ds.read_cursor)

    def blkfile_name(store, dircfg, number=None):
        if number is None:
            number = dircfg['blkfile_number']
        if number > 9999:
            return os.path.join(dircfg['dirname'], "blocks", "blk%05d.dat"
                                % (number - 100000,))
        return os.path.join(dircfg['dirname'], "blk%04d.dat" % (number,))

    def save_blkfile_offset(store, dircfg, offset):
        store.sql("""
            UPDATE datadir
               SET blkfile_number = ?,
                   blkfile_offset = ?
             WHERE datadir_id = ?""",
                  (dircfg['blkfile_number'], store.intin(offset),
                   dircfg['id']))
        if store.rowcount() == 0:
            store.sql("""
                INSERT INTO datadir (datadir_id, dirname, blkfile_number,
                    blkfile_offset, chain_id)
                VALUES (?, ?, ?, ?, ?)""",
                      (dircfg['id'], dircfg['dirname'],
                       dircfg['blkfile_number'],
                       store.intin(offset), dircfg['chain_id']))
        dircfg['blkfile_offset'] = offset

    def _refresh_dircfg(store, dircfg):
        row = store.selectrow("""
            SELECT blkfile_number, blkfile_offset
              FROM datadir
             WHERE dirname = ?""", (dircfg['dirname'],))
        if row:
            number, offset = map(int, row)
            if (number > dircfg['blkfile_number'] or
                (number == dircfg['blkfile_number'] and
                 offset > dircfg['blkfile_offset'])):
                dircfg['blkfile_number'] = number
                dircfg['blkfile_offset'] = offset

    def get_block_number(store, chain_id):
        row = store.selectrow("""
            SELECT block_height
              FROM chain_candidate
             WHERE chain_id = ?
               AND in_longest = 1
             ORDER BY block_height DESC
             LIMIT 1""", (chain_id,))
        return int(row[0]) if row else -1

    def get_target(store, chain_id):
        rows = store.selectall("""
            SELECT b.block_nBits
              FROM block b
              JOIN chain c ON (b.block_id = c.chain_last_block_id)
             WHERE c.chain_id = ?""", (chain_id,))
        return util.calculate_target(int(rows[0][0])) if rows else None

    def get_received_and_last_block_id(store, chain_id, pubkey_hash,
                                       block_height = None):
        sql = """
            SELECT COALESCE(value_sum, 0), c.chain_last_block_id
              FROM chain c LEFT JOIN (
              SELECT cc.chain_id, SUM(txout.txout_value) value_sum
              FROM pubkey
              JOIN txout              ON (txout.pubkey_id = pubkey.pubkey_id)
              JOIN block_tx           ON (block_tx.tx_id = txout.tx_id)
              JOIN block b            ON (b.block_id = block_tx.block_id)
              JOIN chain_candidate cc ON (cc.block_id = b.block_id)
              WHERE
                  pubkey.pubkey_hash = ? AND
                  cc.chain_id = ? AND
                  cc.in_longest = 1""" + (
                  "" if block_height is None else """ AND
                  cc.block_height <= ?""") + """
              GROUP BY cc.chain_id
              ) a ON (c.chain_id = a.chain_id)
              WHERE c.chain_id = ?"""
        dbhash = store.binin(pubkey_hash)

        return store.selectrow(sql,
                               (dbhash, chain_id, chain_id)
                               if block_height is None else
                               (dbhash, chain_id, block_height, chain_id))

    def get_received(store, chain_id, pubkey_hash, block_height = None):
        return store.get_received_and_last_block_id(
            chain_id, pubkey_hash, block_height)[0]

    def get_sent_and_last_block_id(store, chain_id, pubkey_hash,
                                   block_height = None):
        sql = """
            SELECT COALESCE(value_sum, 0), c.chain_last_block_id
              FROM chain c LEFT JOIN (
              SELECT cc.chain_id, SUM(txout.txout_value) value_sum
              FROM pubkey
              JOIN txout              ON (txout.pubkey_id = pubkey.pubkey_id)
              JOIN txin               ON (txin.txout_id = txout.txout_id)
              JOIN block_tx           ON (block_tx.tx_id = txin.tx_id)
              JOIN block b            ON (b.block_id = block_tx.block_id)
              JOIN chain_candidate cc ON (cc.block_id = b.block_id)
              WHERE
                  pubkey.pubkey_hash = ? AND
                  cc.chain_id = ? AND
                  cc.in_longest = 1""" + (
                  "" if block_height is None else """ AND
                  cc.block_height <= ?""") + """
              GROUP BY cc.chain_id
              ) a ON (c.chain_id = a.chain_id)
              WHERE c.chain_id = ?"""
        dbhash = store.binin(pubkey_hash)

        return store.selectrow(sql,
                               (dbhash, chain_id, chain_id)
                               if block_height is None else
                               (dbhash, chain_id, block_height, chain_id))

    def get_sent(store, chain_id, pubkey_hash, block_height = None):
        return store.get_sent_and_last_block_id(
            chain_id, pubkey_hash, block_height)[0]

    def get_balance(store, chain_id, pubkey_hash):
        sent, last_block_id = store.get_sent_and_last_block_id(
            chain_id, pubkey_hash)
        received, last_block_id_2 = store.get_received_and_last_block_id(
            chain_id, pubkey_hash)

        # Deal with the race condition.
        for i in xrange(2):
            if last_block_id == last_block_id_2:
                break

            store.log.debug("Requerying balance: %d != %d",
                          last_block_id, last_block_id_2)

            received, last_block_id_2 = store.get_received(
                chain_id, pubkey_hash, store.get_block_height(last_block_id))

            if last_block_id == last_block_id_2:
                break

            store.log.info("Balance query affected by reorg? %d != %d",
                           last_block_id, last_block_id_2)

            sent, last_block_id = store.get_sent(
                chain_id, pubkey_hash, store.get_block_height(last_block_id_2))

        if last_block_id != last_block_id_2:
            store.log.warning("Balance query failed due to loader activity.")
            return None

        return received - sent


    def firstbits_full(store, version, hash):
        """
        Return the address in lowercase.  An initial substring of this
        will become the firstbits.
        """
        return util.hash_to_address(version, hash).lower()

    def insert_firstbits(store, pubkey_id, block_id, addr_vers, fb):
        store.sql("""
            INSERT INTO abe_firstbits (
                pubkey_id, block_id, address_version, firstbits
            )
            VALUES (?, ?, ?, ?)""",
                  (pubkey_id, block_id, addr_vers, fb))

    def cant_do_firstbits(store, addr_vers, block_id, pubkey_id):
        store.log.info(
            "No firstbits for pubkey_id %d, block_id %d, version '%s'",
            pubkey_id, block_id, store.binout_hex(addr_vers))
        store.insert_firstbits(pubkey_id, block_id, addr_vers, '')

    def do_firstbits(store, addr_vers, block_id, fb, ids, full):
        """
        Insert the firstbits that start with fb using addr_vers and
        are first seen in block_id.  Return the count of rows
        inserted.

        fb -- string, not a firstbits using addr_vers in any ancestor
        of block_id
        ids -- set of ids of all pubkeys first seen in block_id whose
        firstbits start with fb
        full -- map from pubkey_id to full firstbits
        """

        if len(ids) <= 1:
            for pubkey_id in ids:
                store.insert_firstbits(pubkey_id, block_id, addr_vers, fb)
            return len(ids)

        pubkeys = {}
        for pubkey_id in ids:
            s = full[pubkey_id]
            if s == fb:
                store.cant_do_firstbits(addr_vers, block_id, pubkey_id)
                continue
            fb1 = fb + s[len(fb)]
            ids1 = pubkeys.get(fb1)
            if ids1 is None:
                ids1 = set()
                pubkeys[fb1] = ids1
            ids1.add(pubkey_id)

        count = 0
        for fb1, ids1 in pubkeys.iteritems():
            count += store.do_firstbits(addr_vers, block_id, fb1, ids1, full)
        return count

    def do_vers_firstbits(store, addr_vers, block_id):
        """
        Create new firstbits records for block and addr_vers.  All
        ancestor blocks must have their firstbits already recorded.
        """

        address_version = store.binout(addr_vers)
        pubkeys = {}  # firstbits to set of pubkey_id
        full    = {}  # pubkey_id to full firstbits, or None if old

        for pubkey_id, pubkey_hash, oblock_id in store.selectall("""
            SELECT DISTINCT
                   pubkey.pubkey_id,
                   pubkey.pubkey_hash,
                   fb.block_id
              FROM block b
              JOIN block_tx bt ON (b.block_id = bt.block_id)
              JOIN txout ON (bt.tx_id = txout.tx_id)
              JOIN pubkey ON (txout.pubkey_id = pubkey.pubkey_id)
              LEFT JOIN abe_firstbits fb ON (
                       fb.address_version = ?
                   AND fb.pubkey_id = pubkey.pubkey_id)
             WHERE b.block_id = ?""", (addr_vers, block_id)):

            pubkey_id = int(pubkey_id)

            if (oblock_id is not None and
                store.is_descended_from(block_id, int(oblock_id))):
                full[pubkey_id] = None

            if pubkey_id in full:
                continue

            full[pubkey_id] = store.firstbits_full(address_version,
                                                   store.binout(pubkey_hash))

        for pubkey_id, s in full.iteritems():
            if s is None:
                continue

            # This is the pubkey's first appearance in the chain.
            # Find the longest match among earlier firstbits.
            longest, longest_id = 0, None
            substrs = [s[0:(i+1)] for i in xrange(len(s))]
            for ancestor_id, fblen, o_pubkey_id in store.selectall("""
                SELECT block_id, LENGTH(firstbits), pubkey_id
                  FROM abe_firstbits fb
                 WHERE address_version = ?
                   AND firstbits IN (?""" + (",?" * (len(s)-1)) + """
                       )""", tuple([addr_vers] + substrs)):
                if fblen > longest and store.is_descended_from(
                    block_id, int(ancestor_id)):
                    longest, longest_id = fblen, o_pubkey_id

            # If necessary, extend the new fb to distinguish it from
            # the longest match.
            if longest_id is not None:
                (o_hash,) = store.selectrow(
                    "SELECT pubkey_hash FROM pubkey WHERE pubkey_id = ?",
                    (longest_id,))
                o_fb = store.firstbits_full(
                    address_version, store.binout(o_hash))
                max_len = min(len(s), len(o_fb))
                while longest < max_len and s[longest] == o_fb[longest]:
                    longest += 1

            if longest == len(s):
                store.cant_do_firstbits(addr_vers, block_id, pubkey_id)
                continue

            fb = s[0 : (longest + 1)]
            ids = pubkeys.get(fb)
            if ids is None:
                ids = set()
                pubkeys[fb] = ids
            ids.add(pubkey_id)

        count = 0
        for fb, ids in pubkeys.iteritems():
            count += store.do_firstbits(addr_vers, block_id, fb, ids, full)
        return count

    def firstbits_to_addresses(store, fb, chain_id=None):
        dbfb = fb.lower()
        ret = []
        bind = [fb[0:(i+1)] for i in xrange(len(fb))]
        if chain_id is not None:
            bind.append(chain_id)

        for dbhash, vers in store.selectall("""
            SELECT pubkey.pubkey_hash,
                   fb.address_version
              FROM abe_firstbits fb
              JOIN pubkey ON (fb.pubkey_id = pubkey.pubkey_id)
              JOIN chain_candidate cc ON (cc.block_id = fb.block_id)
             WHERE fb.firstbits IN (?""" + (",?" * (len(fb)-1)) + """)""" + ( \
                "" if chain_id is None else """
               AND cc.chain_id = ?"""), tuple(bind)):
            address = util.hash_to_address(store.binout(vers),
                                           store.binout(dbhash))
            if address.lower().startswith(dbfb):
                ret.append(address)

        if len(ret) == 0 or (len(ret) > 1 and fb in ret):
            ret = [fb]  # assume exact address match

        return ret

    def get_firstbits(store, address_version=None, db_pubkey_hash=None,
                      chain_id=None):
        """
        Return address's firstbits, or the longest of multiple
        firstbits values if chain_id is not given, or None if address
        has not appeared, or the empty string if address has appeared
        but has no firstbits.
        """
        vers, dbhash = store.binin(address_version), db_pubkey_hash
        rows = store.selectall("""
            SELECT fb.firstbits
              FROM abe_firstbits fb
              JOIN pubkey ON (fb.pubkey_id = pubkey.pubkey_id)
              JOIN chain_candidate cc ON (fb.block_id = cc.block_id)
             WHERE cc.in_longest = 1
               AND fb.address_version = ?
               AND pubkey.pubkey_hash = ?""" + (
                "" if chain_id is None else """
               AND cc.chain_id = ?"""),
                               (vers, dbhash) if chain_id is None else
                               (vers, dbhash, chain_id))
        if not rows:
            return None

        ret = ""
        for (fb,) in rows:
            if len(fb) > len(ret):
                ret = fb
        return ret

# MULTICHAIN START
    def get_number_of_transactions(store, chain):
        """
        Add up the number of tx in each block which belongs to chain of chain_id
        :param chain_id:
        :return: number of tx, or -1 if there was an error
        """
        result = -1
        sumrow = store.selectrow("""
            SELECT SUM(block_num_tx) FROM chain_summary WHERE chain_id = ?
        """, (chain.id,))
        if sumrow:
            result = sumrow[0]
        return result

    def get_number_of_addresses(store, chain):
        """
        Count the number of unique pubkeys found in txouts for a chain_id
        :param chain_id:
        :return: number of addresses, or -1 if there was an error
        """
        result = -1
        countrow = store.selectrow("""
            SELECT COUNT(DISTINCT(pubkey_hash)) FROM txout_detail WHERE chain_id = ?
        """, (chain.id,))
        if countrow:
            result = countrow[0]
            if result > 0:
                result -= 1  # NULL_PUBKEY_HASH
        return result

    def get_number_of_assets(store, chain):
        """
        Get the number of assets issued in a chain
        :param chain:
        :return: integer number of assets
        """
        resp = store.get_assets(chain)
        if resp is not None:
            return len(resp)
        return 0

    def get_assets(store, chain):
        """
        Get the result of listassets json-rpc command as json object
        :param chain:
        :return: json object
        """
        url = store.get_url_by_chain(chain)
        multichain_name = store.get_multichain_name_by_id(chain.id)
        resp = None
        try:
            resp = util.jsonrpc(multichain_name, url, "listassets")
        except util.JsonrpcException as e:
            raise Exception("JSON-RPC error({0}): {1}".format(e.code, e.message))
        except IOError as e:
            raise e
        return resp

    def get_asset_by_name(store, chain, name):
        """
        Get the asset by name from listassets json-rpc command as json object
        :param chain:
        :return: json object
        """
        url = store.get_url_by_chain(chain)
        multichain_name = store.get_multichain_name_by_id(chain.id)
        resp = None
        try:
            resp = util.jsonrpc(multichain_name, url, "listassets", name)
            if len(resp) > 0 :
                resp = resp[0]
        except util.JsonrpcException as e:
            raise Exception("JSON-RPC error({0}): {1}".format(e.code, e.message))
        except IOError as e:
            raise e
        return resp

    def get_block_by_hash(store, chain, blockhash):
        """
        Get block info from getblock json-rpc command as json object
        :param chain:
        :param blockhash: hex string of block hash
        :return: json object
        """
        url = store.get_url_by_chain(chain)
        multichain_name = store.get_multichain_name_by_id(chain.id)
        resp = None
        try:
            resp = util.jsonrpc(multichain_name, url, "getblock", blockhash)
        except util.JsonrpcException as e:
            raise Exception("JSON-RPC error({0}): {1}".format(e.code, e.message))
        except IOError as e:
            raise e
        return resp

    def get_number_of_peers(store, chain):
        Get the number of connected peers
        :return: Integer number of nodes
        resp = store.get_peerinfo(chain)

    def get_peerinfo(store, chain):
        multichain_name = store.get_multichain_name_by_id(chain.id)
        resp = util.jsonrpc(multichain_name, url, "getpeerinfo")

    def get_number_of_asset_holders(store, chain, assetref):
        """
        Get the number of addresses holding units of an asset
        :param chain:
        :param assetref:
        :return: int
        """
        chain_id = chain.id
        prefix = int( assetref.split('-')[-1] )
        row = store.selectrow("""
            SELECT count(DISTINCT pubkey_id)
            FROM asset_address_balance
            WHERE balance>0 AND asset_id=( SELECT asset_id FROM asset WHERE chain_id=? AND prefix=?)
            """, (chain_id, prefix))
        if row is None:
            result = 0
        else:
            result = int(row[0])
        return result

    def get_asset_holders(store, chain, assetref):
        """
        Get a list of the addresses holding units of an asset
        :param chain:
        :param assetref:
        :return: List or None, where each list element is a dictionary storing the pubkey and balance.
        """
        def parse_row(row):
            pubkey, pubkey_hash, pubkey_flags, balance = row
            ret = {
                "pubkey": store.binout(pubkey),
                "pubkey_hash": store.binout(pubkey_hash),
                "pubkey_flags": pubkey_flags,
                "balance": balance
                }
            return ret

        chain_id = chain.id
        prefix = int( assetref.split('-')[-1] )
        rows = store.selectall("""
            SELECT p.pubkey, p.pubkey_hash, p.pubkey_flags, a.balance
            FROM asset_address_balance a
            JOIN pubkey p ON (a.pubkey_id = p.pubkey_id)
            WHERE balance>0 AND asset_id=( SELECT asset_id FROM asset WHERE chain_id=? AND prefix=?)
            """, (chain_id, prefix))
        if rows is None:
            return None
        result = list(map(parse_row, rows))
        return result

    def get_recent_transactions_as_json(store, chain, limit=10):

        rows = store.selectall("""
            SELECT DISTINCT tx_hash
            FROM txout_detail
            WHERE chain_id=? AND pubkey_id != ?
            ORDER BY block_height DESC, tx_id DESC
            LIMIT ?
        """, (chain.id, NULL_PUBKEY_ID, limit))

        if rows is None:
             return []

        result = []
        for row in rows:
            try:
                txid = store.hashout_hex(row[0])
                json = store.get_rawtransaction_decoded(chain, txid)
                if json is not None and json['confirmations']>0:
                    result.append(json)
            except Exception:
                pass

        return result

    def get_transactions_for_asset(store, chain, assetref):
        """
        Get a list of transactions related to an asset.
        :param chain:
        :param assetref:
        :return: list of data (tx hash, height, blockhash) or None.
        """
        def parse_row(row):
            txhash, height, blockhash = row
            ret = {
#                "outpos": int(pos),
                "hash": store.hashout_hex(txhash),
                "height": int(height),
                "blockhash": store.hashout_hex(blockhash)
                }
            return ret

        prefix = int( assetref.split('-')[-1] )
        rows = store.selectall("""
            select DISTINCT t.tx_hash, bb.block_height, bb.block_hash from asset_txid a
            join block_tx b on (a.tx_id=b.tx_id)
            join tx t on (a.tx_id=t.tx_id)
            join block bb on (b.block_id=bb.block_id)
            where a.asset_id=( SELECT asset_id FROM asset WHERE chain_id=? AND prefix=?)
            order by bb.block_height, b.tx_pos asc
        """, (chain.id, prefix))

        if rows is None:
            return None

        result = list(map(parse_row, rows))
        return result

    def get_transactions_for_asset_address(store, chain, assetref, address):
        """
        Get a list of transactions related to both an address and an assetref
        :param chain:
        :param assetref:
        :param address:
        :return: List of transactions or none.
        """
        def parse_row(row):
            txhash, height, blockhash = row
            ret = {
                #"outpos": int(pos),
                "hash": store.hashout_hex(txhash),
                "height": int(height),
                "blockhash": store.hashout_hex(blockhash)
                }
            return ret

        # get pubkey id
        version, pubkeyhash = util.decode_check_address_multichain(address)
        if pubkeyhash is None:
            return None
        row = store.selectrow("""select pubkey_id from pubkey where pubkey_hash = ?""",
                                    (store.binin(pubkeyhash),) )
        if row is None:
            return None
        pubkey_id = int(row[0])

        prefix = int( assetref.split('-')[-1] )
        # a.txout_pos,... , a.txout_pos asc
        rows = store.selectall("""
            select DISTINCT t.tx_hash, bb.block_height, bb.block_hash from asset_txid a
            join block_tx b on (a.tx_id=b.tx_id)
            join tx t on (a.tx_id=t.tx_id)
            join block bb on (b.block_id=bb.block_id)
            join txout o on (a.tx_id=o.tx_id)
            join txin_detail i on (a.tx_id=i.tx_id)
            where a.asset_id=( SELECT asset_id FROM asset WHERE chain_id=? AND prefix=?)
            and (o.pubkey_id=? OR i.pubkey_id=?)
            order by bb.block_height, b.tx_pos asc
        """, (chain.id, prefix, pubkey_id, pubkey_id))

        if rows is None:
            return None

        result = list(map(parse_row, rows))
        return result

    def get_number_of_transactions_for_asset_address(store, chain, assetref, pubkey_id):
        """
        Get the number of transactions related to both an asset and an address.
        :param chain:
        :param assetref: human readable assetref e.g. 111-222-333
        :param pubkey_id:
        :return:
        """
        prefix = int( assetref.split('-')[-1] )
        row = store.selectrow("""
            select count(distinct a.tx_id) from asset_txid a join txout o on (a.tx_id=o.tx_id)
            where a.asset_id=( SELECT asset_id FROM asset WHERE chain_id=? AND prefix=?)
            and o.pubkey_id=?
        """, (chain.id, prefix, pubkey_id))
        if row is None:
            return 0
        return int(row[0])

    def get_number_of_transactions_for_asset(store, chain, assetref):
        """
        Get the number of transactions related to an asset which are stored in the database.
        :param chain:
        :param assetref: human readable assetref e.g. 111-222-333
        :return: int
        """
        prefix = int( assetref.split('-')[-1] )
        row = store.selectrow("""
            select count(distinct a.tx_id) from asset_txid a
            where a.asset_id=( SELECT asset_id FROM asset WHERE chain_id=? AND prefix=?)
        """, (chain.id, prefix))
        if row is None:
            return 0
        return int(row[0])


    def list_transactions(store, chain, count):
        """
        Get the result of listtransactions json-rpc command as json object
        NOTE: This call does not work with MultiChain v2 scalable wallets.
        :param chain:
        :return: json object
        """
        url = store.get_url_by_chain(chain)
        multichain_name = store.get_multichain_name_by_id(chain.id)
        resp = None
        try:
            resp = util.jsonrpc(multichain_name, url, "listtransactions", "*", count)
        except util.JsonrpcException as e:
            raise Exception("JSON-RPC error({0}): {1}".format(e.code, e.message))
        except IOError as e:
            raise e
        return resp

    def get_number_of_streams(store, chain):
        resp = store.list_streams(chain)
        if resp is not None:
            return len(resp)
        return 0

    def list_stream(store, chain, name):
        """
        Get the result of liststreams json-rpc command as json object.
        We ask for a specific stream and verbose data.
        :param chain:
        :param name:
        :return: None or json object for the stream
        """
        url = store.get_url_by_chain(chain)
        multichain_name = store.get_multichain_name_by_id(chain.id)
        resp = None
        try:
            resp = util.jsonrpc(multichain_name, url, "liststreams", name, True)

        if len(resp) < 1:
            return None
        return resp[0]

    def list_streams(store, chain, count=0):
            # liststreans streamref verbose count start
            # e.g. liststreams "*" true 2 -2
            # display last two streams.
            # e.g. liststreams "*" true 2 0
            # display first two streams

            # all streams
            if count <= 0:
                resp = util.jsonrpc(multichain_name, url, "liststreams", "*", True)
            else:
                resp = util.jsonrpc(multichain_name, url, "liststreams", "*", True, count, -count)


    def list_stream_items(store, chain, streamref, count=10, start=-10):
        """
        Get the result of liststreamitems json-rpc command as json object.
        We ask for all streams and verbose data, such as the creators field.
        :param chain:
        :param streamref:
        :param count:
        :param start:
        :return: json object
        """
        url = store.get_url_by_chain(chain)
        multichain_name = store.get_multichain_name_by_id(chain.id)
        resp = None
        try:
            # liststreamitems streamref verbose count start localordering
            resp = util.jsonrpc(multichain_name, url, "liststreamitems", streamref, True, count, start)
        except util.JsonrpcException as e:
            raise Exception("JSON-RPC error({0}): {1}".format(e.code, e.message))
        except IOError as e:
            raise e
        return resp

    def list_stream_publisher_items(store, chain, streamref, publisher, count=10, start=-10):
        """
        Get the result of liststreampublisheritems json-rpc command as json object.
        We ask for all streams and verbose data, such as the creators field.
        :param chain:
        :param streamref:
        :param publisher:
        :param count:
        :param start:
        :return: json object
        """
        url = store.get_url_by_chain(chain)
        multichain_name = store.get_multichain_name_by_id(chain.id)
        resp = None
        try:
            # liststreampublisheritems streamref publisheraddress verbose count start localordering
            resp = util.jsonrpc(multichain_name, url, "liststreampublisheritems", streamref, publisher, True, count, start)
        except util.JsonrpcException as e:
            raise Exception("JSON-RPC error({0}): {1}".format(e.code, e.message))
        except IOError as e:
            raise e
        return resp

    def list_stream_publishers(store, chain, streamref, publisher="*"):
        """
        Get the result of liststreampublisheritems json-rpc command as json object.
        We ask for all streams and verbose data, such as the creators field.
        :param chain:
        :param streamref:
        :param publisher:
        :return: json object
        """
        url = store.get_url_by_chain(chain)
        multichain_name = store.get_multichain_name_by_id(chain.id)
        resp = None
        try:
            # liststreampublishers streamref publisheraddress
            resp = util.jsonrpc(multichain_name, url, "liststreampublishers", streamref, publisher)
        except util.JsonrpcException as e:
            raise Exception("JSON-RPC error({0}): {1}".format(e.code, e.message))
        except IOError as e:
            raise e
        return resp

    def list_stream_keys(store, chain, streamref, keys="*"):
        """
        Get the result of liststreamkeys json-rpc command as json object.
        We ask for all keys and verbose data, such as the creators field.
        :param chain:
        :param streamref:
        :param keys:
        :return: json object
        """
        url = store.get_url_by_chain(chain)
        multichain_name = store.get_multichain_name_by_id(chain.id)
        resp = None
        try:
            # liststreamkeys streamref keys
            resp = util.jsonrpc(multichain_name, url, "liststreamkeys", streamref, keys)
        except util.JsonrpcException as e:
            raise Exception("JSON-RPC error({0}): {1}".format(e.code, e.message))
        except IOError as e:
            raise e
        return resp

    def list_stream_key_items(store, chain, streamref, streamkey, count=10, start=-10):
        """
        Get the result of liststreamkeyitems json-rpc command as json object.
        We ask for all streams and verbose data, such as the creators field.
        :param chain:
        :param streamref:
        :param key:
        :param count:
        :param start:
        :return: json object
        """
        url = store.get_url_by_chain(chain)
        multichain_name = store.get_multichain_name_by_id(chain.id)
        resp = None
        try:
            # liststreamkeyitems streamref publisheraddress verbose count start localordering
            resp = util.jsonrpc(multichain_name, url, "liststreamkeyitems", streamref, streamkey, True, count, start)
        except util.JsonrpcException as e:
            raise Exception("JSON-RPC error({0}): {1}".format(e.code, e.message))
        except IOError as e:
            raise e
        return resp

    def get_rawmempool(store, chain):
        """
        Get the result of getrawmempool json-rpc command as json object
        :param chain:
        :return: json object (key is txid, value is dict)
        """
        url = store.get_url_by_chain(chain)
        multichain_name = store.get_multichain_name_by_id(chain.id)
        resp = None
            resp = util.jsonrpc(multichain_name, url, "getrawmempool", True)

    def get_rawtransaction_decoded(store, chain, tx_hash):
        resp = util.jsonrpc(multichain_name, url, "getrawtransaction", tx_hash, 1)

    def get_labels_for_tx(store, tx_hash, chain):
            mytx = store._export_tx_detail(tx_hash, chain)
        except MalformedHash:
            mytx = None

        if mytx is not None:
            d = set()
            for txout in mytx['out']:
                tmp = store.get_labels_for_scriptpubkey(chain, txout['binscript'])
                d |= set(tmp)
            labels = list(d)
        return labels

    def get_labels_for_scriptpubkey(store, chain, scriptpubkey):
        """
        Get labels describing the scriptpubkey of a txout.
        :param chain:
        :param scriptpubkey:
        :return: labels as list, or empty list if not a recognized MultiChain OP_DROP or OP_RETURN.
        """
        label = []
        script_type, data = chain.parse_txout_script(scriptpubkey)
        if script_type is Chain.SCRIPT_TYPE_MULTICHAIN_P2SH:
            label.append('P2SH')
        if script_type in [Chain.SCRIPT_TYPE_MULTICHAIN_STREAM,
            Chain.SCRIPT_TYPE_MULTICHAIN_STREAM_ITEM]:
            label.append('Stream')
        if script_type in [Chain.SCRIPT_TYPE_MULTICHAIN, Chain.SCRIPT_TYPE_MULTICHAIN_P2SH]:
            data = util.get_multichain_op_drop_data(scriptpubkey)
            if data is not None:
                opdrop_type, val = util.parse_op_drop_data(data, chain)
                if opdrop_type==util.OP_DROP_TYPE_ISSUE_ASSET:
                    label.append('Asset')
                elif opdrop_type==util.OP_DROP_TYPE_SEND_ASSET:
                    label.append('Asset')
                elif opdrop_type==util.OP_DROP_TYPE_PERMISSION:
                    label.append('Permissions')
                elif opdrop_type==util.OP_DROP_TYPE_ISSUE_MORE_ASSET:
                    label.append('Asset')
                else:
                    label.append('OP_DROP')
            else:
                label.append('Unknown')
        elif script_type is Chain.SCRIPT_TYPE_MULTICHAIN_OP_RETURN:
            opreturn_type, val = util.parse_op_return_data(data, chain)
            if opreturn_type==util.OP_RETURN_TYPE_ISSUE_ASSET:
                label.append('Asset')
            else:
                label.append('Metadata')
        # Protocol 10007
        elif script_type in [Chain.SCRIPT_TYPE_MULTICHAIN_SPKN, Chain.SCRIPT_TYPE_MULTICHAIN_SPKU]:
            data = util.get_multichain_op_drop_data(scriptpubkey)
            if data is not None:
                opdrop_type, val = util.parse_op_drop_data(data, chain)
                if opdrop_type==util.OP_DROP_TYPE_FOLLOW_ON_ISSUANCE_METADATA:
                    label.append('Asset')
                elif opdrop_type==util.OP_DROP_TYPE_SPKN_NEW_ISSUE:
                    label.append('Asset')
                elif opdrop_type==util.OP_DROP_TYPE_SPKN_CREATE_STREAM:
                    label.append('Stream')
                elif opdrop_type==util.OP_DROP_TYPE_SPKE:
                    pass
                    #label.append('SPKE')
            else:
                label.append('Unknown')
        elif script_type is Chain.SCRIPT_TYPE_MULTICHAIN_ENTITY_PERMISSION:
            label.append('Permissions')
        return label
