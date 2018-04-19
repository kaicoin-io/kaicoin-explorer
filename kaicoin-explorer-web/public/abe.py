            '<table class="table table-striped">\n',
            '<tr><th>Status</th>',
            '<th>Chain</th>',
            '<th>Blocks</th>',
            '<th>Transactions</th>',
            '<th>Assets</th>',
            '<th>Addresses</th>',
            '<th>Streams</th>',
            '<th>Peers</th>'
            '<th>Started</th><th>Age (days)</th>',
            '</tr>\n']
        now = time.time() - EPOCH1970

        rows = abe.store.selectall("""
            SELECT
		   c.chain_name, b.block_height, b.block_nTime, b.block_hash,
                   b.block_total_seconds, b.block_total_satoshis,
                   b.block_satoshi_seconds,
                   b.block_total_ss
              FROM chain c
              JOIN block b ON (c.chain_last_block_id = b.block_id)
             ORDER BY c.chain_name
            """)

            num_txs = abe.store.get_number_of_transactions(chain)
            num_addresses = abe.store.get_number_of_addresses(chain)
            connection_status = True

            num_peers = abe.store.get_number_of_peers(chain)
            num_assets = abe.store.get_number_of_assets(chain)
            num_streams = abe.store.get_number_of_streams(chain)

            if row[6] is not None and row[7] is not None:
                (seconds, satoshis, ss, total_ss) = (
                    int(row[4]), int(row[5]), int(row[6]), int(row[7]))

            started = nTime - seconds
            chain_age = now - started
            since_block = now - nTime


    def handle_recent(abe, page):

        mempool = abe.store.get_rawmempool(chain)
        recenttx = abe.store.get_recent_transactions_as_json(chain, 10)

        sorted_mempool = sorted(mempool.items()[:10], key=lambda tup: tup[1]['time'], reverse=True)

        for (k, v) in sorted_mempool:  # mempool.iteritems():
            txid = k
            diff = int(now - v['time'])
            if diff < 60:
                elapsed = "< 1 minute"
            elif diff < 3600:
                elapsed = "< " + str(int((diff / 60)+0.5)) + " minutes"
            elif diff < 3600*24*2:
                elapsed = "< " + str(int(diff / 3600)) + " hours"
            else:
                elapsed = str(int((diff / 3600) / 24)) + " days"
                    json = abe.store.get_rawtransaction_decoded(chain, txid)

                if json is not None:
                    scriptpubkeys = [vout['scriptPubKey']['hex'] for vout in json['vout']]
                    labels = None
                    d = set()
                    for hex in scriptpubkeys:
                        binscript = binascii.unhexlify(hex)
                        tmp = abe.store.get_labels_for_scriptpubkey(chain, binscript)
                        d |= set(tmp)
                    labels = list(d)

            if labels is None:
            for label in labels:
                body += ['&nbsp;<span class="label label-primary">',label,'</span>']

            body += ['</td><td>']
            conf = v.get('confirmations', None)
            if conf is None or conf == 0:
                body += ['<span class="label label-default">Mempool</span>']
            else:
                body += ['<span class="label label-info">', conf, ' confirmations</span>']

            info_resp = util.jsonrpc(multichain_name, url, "getinfo")
            params_resp = util.jsonrpc(multichain_name, url, "getblockchainparams")



    def _show_block(abe, page, dotdotblock, chain, **kwargs):
        body = page['body']

        try:
            b = abe.store.export_block(chain, **kwargs)
        except DataStore.MalformedHash:
            body += ['<p class="error">Not in correct format.</p>']
            return

        if b is None:
            body += ['<p class="error">Block not found.</p>']
            return

        in_longest = False
        for cc in b['chain_candidates']:
            if chain is None:
                chain = cc['chain']
            if chain.id == cc['chain'].id:
                in_longest = cc['in_longest']


    def handle_block(abe, page):
        abe._show_block(page, '', None, block_hash=block_hash)
        tx = abe.store.export_tx(tx_hash = tx_hash, format = 'browser')
        return abe.show_tx(page, tx)


    def show_mempool_tx_json(abe, page, tx):

        def row_to_html(row, this_ch, other_ch, no_link_text):

            if novalidaddress is False:
                if this_ch is 'i':
                try:
                        resp = util.jsonrpc(chain_name, chain_url, "getrawtransaction", txid, 1)
                        n = int(vout)
                        addressLabel = resp['vout'][n]['scriptPubKey']['addresses'][0]
                        value = resp['vout'][n]['value']
                else:
                        addressLabel = row['scriptPubKey']['addresses'][0]
                        value = row['value']

        asset_txid_dict = abe.get_assets_by_txid_fragment(chain)

        chain_name = abe.store.get_multichain_name_by_id(chain.id)
        chain_url = abe.store.get_url_by_chain(chain)

        body += html_keyvalue_tablerow('Appeared in', escape(chain.name) + ' (Mempool)')
        body += html_keyvalue_tablerow('Number of inputs', len(tx['vin']),
            ' &ndash; <a href="#inputs">jump to inputs</a>')
        body += html_keyvalue_tablerow('Number of outputs', len(tx['vout']),
            ' &ndash; <a href="#outputs">jump to outputs</a>')
        body += html_keyvalue_tablerow('Size', len(tx['hex']), ' bytes')
        body += ['</table>']


    def handle_address(abe, page):
        version, pubkeyhash = util.decode_check_address_multichain(address)
        body += ['<h3>Permissions</h3>']
        try:
            resp = util.jsonrpc(multichain_name, url, "listpermissions", "all", address)
            if len(resp) > 0 :
                body += ['<ul>']
                for permission in resp:
                    name = permission['type'].capitalize()
                    start = permission['startblock']
                    end = permission['endblock']
                    range = ""
                    if not (start==0 and end==4294967295):
                        range = " (blocks {0} - {1} only)".format(start, end)
                    body += ['<li>', name, range, '</li>']
                body += ['</ul>']

        # Display native currency if the blockchain has one
        if abe.get_blockchainparams(chain).get('initial-block-reward', 0) > 0:
            body += ['<h3>Native Balance</h3>']
            try:
                resp = util.jsonrpc(multichain_name, url, "getaddressbalances", address)
                if len(resp) is 0:
                    body += ['None']
                else:
                    body += ['<ul>']
                    for balance in resp:
                        if str(balance['assetref']) is '':
                            body += ['<li>', str(balance['qty']), '</li>']
                    body += ['</ul>']

        body += ['<h3>Asset Balances</h3>']
        try:
            row = abe.store.selectrow("""select pubkey_id from pubkey where pubkey_hash = ?""",
                                      (abe.store.binin(pubkeyhash),) )
            assets_resp = abe.store.get_assets(chain)

    # Given an address and asset reference, show transactions for that address and asset
    def handle_assetaddress(abe, page):
        resp = util.jsonrpc(multichain_name, url, "listassets", assetref)


    # local method to get raw units for a given asset from a txin or txout,
    def get_asset_amount_from_txinout(tx, this_ch, other_ch, asset, chain):

        # local method to get raw units for a given asset from a txin or txout,
        def get_asset_amount_from_txinout(tx, this_ch, other_ch, asset, chain):
            binaddr = tx['binaddr']
            if binaddr is None:
                return 0
            binscript = tx['binscript']
            if binscript is None:
                return 0
            # for input, we want to examine the txout it represents
            if this_ch=='i':
                binscript = tx['multichain_scriptPubKey']
            script_type, data = chain.parse_txout_script(binscript)
            if script_type not in [Chain.SCRIPT_TYPE_MULTICHAIN, Chain.SCRIPT_TYPE_MULTICHAIN_P2SH]:
                return 0
            data = util.get_multichain_op_drop_data(binscript)
            if data is None:
                return 0
            opdrop_type, val = util.parse_op_drop_data(data, chain)
            if opdrop_type==util.OP_DROP_TYPE_ISSUE_ASSET:
                return val
            elif opdrop_type==util.OP_DROP_TYPE_SEND_ASSET:
                for dict in val:
                    quantity = dict['quantity']
                    assetref = dict['assetref']
                    if assetref == asset['assetref']:
                        return quantity


    # Page to show the assets that exist on a chain
    def handle_assets(abe, page):
        multichain_name = abe.store.get_multichain_name_by_id(chain.id)
        try:
            resp = util.jsonrpc(multichain_name, url, "listassets")
            num_assets = len(resp)

        # Show any unconfirmed assets
        if unconfirmed is False:
            return
        body += ['<h3>Unconfirmed Assets</h3>']

        body += ['<table class="table table-striped"><tr><th>Asset Name</th><th>Asset Reference</th>'
                 '<th>Issue Transaction</th>'
                 '<th>Asset Holders</th>'
                 '<th>Transactions</th>'
                 '<th>Issued Quantity</th><th>Units</th>'
                 '</tr>']
        for asset in resp:
            issueqty = util.format_display_quantity(asset, asset['issueqty'])


    # Page to show the streams that exist on a chain
    def handle_streams(abe, page):

        body += ['<h3>Streams</h3>']
        body += ['<table class="table table-striped">'
                 '<tr><th>Stream Name</th>'
                 '<th>Stream Items</th>'
                 '<th>Anybody Can Publish</th>'
                 '<th>Creator</th>'
                 '<th>Creation Transaction</th>'
                 '</tr>']


    def do_rpc_txoutdata(abe, page, chain):
        url = abe.store.get_url_by_chain(chain)
        resp = util.jsonrpc(chain_name, url, "gettxoutdata", txid, int(vout))


    def do_rpc_tx(abe, page, chain):
        tx = abe.store.export_tx(tx_hash=tx_hash.lower(), format='browser')
        chain_name = abe.store.get_multichain_name_by_id(chain.id)
        url = abe.store.get_url_by_chain(chain)
            resp = util.jsonrpc(chain_name, url, "getrawtransaction", tx_hash, decode_json_flag)
        return s

    def handle_mempooltx(abe, page):
        chain_name = abe.store.get_multichain_name_by_id(chain.id)
        url = abe.store.get_url_by_chain(chain)
            resp = util.jsonrpc(chain_name, url, "getrawtransaction", tx_hash, 1)
        return abe.show_mempool_tx_json(page, resp)

    def handle_deprecatedaddress(abe, page):
            history = abe.store.export_address_history(
                address, chain=page['chain'], max_rows=abe.address_history_rows_max)

        def format_amounts(amounts, link):
            ret = []
            for chain in chains:
                if ret:
                    ret += [', ']
                ret += [format_satoshis(amounts[chain.id], chain),
                        ' ', escape(chain.code3)]
                if link:
                    vers = chain.address_version
                    if page['chain'] is not None and version == page['chain'].script_addr_vers:
                        vers = chain.script_addr_vers or vers
                    checksum = chain.address_checksum
                    if checksum is None:
                        other = util.hash_to_address(vers, binaddr)
                    else:
                        other = util.hash_to_address_multichain(vers, binaddr, checksum)
                    if other != address:
                        ret[-1] = ['<a href="', page['dotdot'],
                                   'address/', other,
                                   '">', ret[-1], '</a>']
            return ret


    def search_number(abe, n):

        return map(process, abe.store.selectall("""
            SELECT c.chain_name, b.block_hash, cc.in_longest
              FROM chain c
              JOIN chain_candidate cc ON (cc.chain_id = c.chain_id)
              JOIN block b ON (b.block_id = cc.block_id)
             WHERE cc.block_height = ?
             ORDER BY c.chain_name, cc.in_longest DESC
        """, (n,)))


    def search_address_prefix(abe, ap):
        """
        Naive method to search for an address.
        :param ap: string containing first few characters of an address
        :return: list of matches
        """

        ret = []

        # Only search the first chain for now
        chain = abe.store.get_chain_by_id(1)
        address_version = chain.address_version
        checksum = chain.address_checksum

        def process(row):
            hash = abe.store.binout(row[0])
            if hash is None:
                return None
            address = util.hash_to_address_multichain(address_version, hash, checksum)
            if not address.lower().startswith(ap.lower()):
                return None
            return abe._found_address(address)

        ret += filter(None, map(process, abe.store.selectall("SELECT pubkey_hash FROM pubkey" )))
        return

        while l >= minlen:
            vl, hl = util.decode_address(al)
            vh, hh = util.decode_address(ah)
            if ones:
                if not all_ones and \
                        util.hash_to_address('\0', hh)[ones:][:1] == '1':
                    break
            elif vh == '\0':
                break
            elif vh != vl and vh != incr_str(vl):
                continue
            if hl <= hh:
                neg = ""
            else:
                neg = " NOT"
                hl, hh = hh, hl
            bl = abe.store.binin(hl)
            bh = abe.store.binin(hh)
            ret += filter(None, map(process, abe.store.selectall(
                "SELECT pubkey_hash FROM pubkey WHERE pubkey_hash" +
                # XXX hardcoded limit.
                neg + " BETWEEN ? AND ? LIMIT 100", (bl, bh))))
            l -= 1
            al = al[:-1]
            ah = ah[:-1]

        return ret


    def do_unspent(abe, page, chain):
        addrs = wsgiref.util.shift_path_info(page['env'])
        addrs = addrs.split("|")
        if len(addrs) < 1 or len(addrs) > MAX_UNSPENT_ADDRESSES:
            return 'Number of addresses must be between 1 and ' + \
                str(MAX_UNSPENT_ADDRESSES)

        if chain:
            chain_id = chain.id
            bind = [chain_id]
        else:
            chain_id = None
            bind = []

        hashes = []
        good_addrs = []
        for address in addrs:
            try:
                hashes.append(abe.store.binin(
                        base58.bc_address_to_hash_160(address)))
                good_addrs.append(address)
            except Exception:
                pass
        addrs = good_addrs
        bind += hashes

        if len(hashes) == 0:  # Address(es) are invalid.
            return 'Error getting unspent outputs'  # blockchain.info compatible

        placeholders = "?" + (",?" * (len(hashes)-1))

        max_rows = abe.address_history_rows_max
        if max_rows >= 0:
            bind += [max_rows + 1]

        spent = set()
        for txout_id, spent_chain_id in abe.store.selectall("""
            SELECT txin.txout_id, cc.chain_id
              FROM chain_candidate cc
              JOIN block_tx ON (block_tx.block_id = cc.block_id)
              JOIN txin ON (txin.tx_id = block_tx.tx_id)
              JOIN txout prevout ON (txin.txout_id = prevout.txout_id)
              JOIN pubkey ON (pubkey.pubkey_id = prevout.pubkey_id)
             WHERE cc.in_longest = 1""" + ("" if chain_id is None else """
               AND cc.chain_id = ?""") + """
               AND pubkey.pubkey_hash IN (""" + placeholders + """)""" + (
                "" if max_rows < 0 else """
             LIMIT ?"""), bind):
            spent.add((int(txout_id), int(spent_chain_id)))

        abe.log.debug('spent: %s', spent)

        received_rows = abe.store.selectall("""
            SELECT
                txout.txout_id,
                cc.chain_id,
                tx.tx_hash,
                txout.txout_pos,
                txout.txout_scriptPubKey,
                txout.txout_value,
                cc.block_height
              FROM chain_candidate cc
              JOIN block_tx ON (block_tx.block_id = cc.block_id)
              JOIN tx ON (tx.tx_id = block_tx.tx_id)
              JOIN txout ON (txout.tx_id = tx.tx_id)
              JOIN pubkey ON (pubkey.pubkey_id = txout.pubkey_id)
             WHERE cc.in_longest = 1""" + ("" if chain_id is None else """
               AND cc.chain_id = ?""") + """
               AND pubkey.pubkey_hash IN (""" + placeholders + """)""" + (
                "" if max_rows < 0 else """
             ORDER BY cc.block_height,
                   block_tx.tx_pos,
                   txout.txout_pos
             LIMIT ?"""), bind)

        if 0 <= max_rows < len(received_rows):
            return "ERROR: too many records to process"

        rows = []
        for row in received_rows:
            key = (int(row[0]), int(row[1]))
            if key in spent:
                continue
            rows.append(row[2:])

        if len(rows) == 0:
            return 'No free outputs to spend [' + '|'.join(addrs) + ']'

        out = []
        for row in rows:
            tx_hash, out_pos, script, value, height = row
            tx_hash = abe.store.hashout_hex(tx_hash)
            out_pos = None if out_pos is None else int(out_pos)
            script = abe.store.binout_hex(script)
            value = None if value is None else int(value)
            height = None if height is None else int(height)
            out.append({
                    'tx_hash': tx_hash,
                    'tx_output_n': out_pos,
                    'script': script,
                    'value': value,
                    'value_hex': None if value is None else "%x" % value,
                    'block_number': height})
        return json.dumps({ 'unspent_outputs': out }, sort_keys=True, indent=2)


    def get_max_block_height(abe, chain):
        # "getblockcount" traditionally returns max(block_height),
        # which is one less than the actual block count.
        return abe.store.get_block_number(chain.id)

    def q_getblockcount(abe, page, chain):
        """shows the current block number."""
        if chain is None:
            return 'Shows the greatest block height in CHAIN.\n' \
                '/chain/CHAIN/q/getblockcount\n'
        return abe.get_max_block_height(chain)

    def q_getdifficulty(abe, page, chain):
        """shows the last solved block's difficulty."""
        if chain is None:
            return 'Shows the difficulty of the last block in CHAIN.\n' \
                '/chain/CHAIN/q/getdifficulty\n'
        target = abe.store.get_target(chain.id)
        return "" if target is None else util.target_to_difficulty(target)

    def q_translate_address(abe, page, chain):
        """shows the address in a given chain with a given address's hash."""
            return 'Translates ADDRESS for use in CHAIN.\n' \
                '/chain/CHAIN/q/translate_address/ADDRESS\n'
        version, hash = util.decode_check_address_multichain(addr)
        if hash is None:
            return addr + " (INVALID ADDRESS)"
        return util.hash_to_address(chain.address_version, hash)

    def q_decode_address(abe, page, chain):
        """shows the version prefix and hash encoded in an address."""
            return "Shows ADDRESS's version byte(s) and public key hash" \
                ' as hex strings separated by colon (":").\n' \
                '/q/decode_address/ADDRESS\n'
        # XXX error check?
        version, hash = util.decode_address(addr)
        ret = version.encode('hex') + ":" + hash.encode('hex')
        if util.hash_to_address(version, hash) != addr:
            ret = "INVALID(" + ret + ")"
        return ret

    def q_addresstohash(abe, page, chain):
        """shows the public key hash encoded in an address."""
        addr = wsgiref.util.shift_path_info(page['env'])
        if addr is None:
            return 'Shows the 160-bit hash encoded in ADDRESS.\n' \
                'For BBE compatibility, the address is not checked for' \
                ' validity.  See also /q/decode_address.\n' \
                '/q/addresstohash/ADDRESS\n'
        version, hash = util.decode_address(addr)
        return hash.encode('hex').upper()

    def q_hashtoaddress(abe, page, chain):
        """shows the address with the given version prefix and hash."""
        arg1 = wsgiref.util.shift_path_info(page['env'])
        arg2 = wsgiref.util.shift_path_info(page['env'])
        if arg1 is None:
            return \
                'Converts a 160-bit hash and address version to an address.\n' \
                '/q/hashtoaddress/HASH[/VERSION]\n'

        if page['env']['PATH_INFO']:
            return "ERROR: Too many arguments"

        if arg2 is not None:
            # BBE-compatible HASH/VERSION
            version, hash = arg2, arg1

        elif arg1.find(":") >= 0:
            # VERSION:HASH as returned by /q/decode_address.
            version, hash = arg1.split(":", 1)

        elif chain:
            version, hash = chain.address_version.encode('hex'), arg1

        else:
            # Default: Bitcoin address starting with "1".
            version, hash = '00', arg1

        try:
            hash = hash.decode('hex')
            version = version.decode('hex')
        except Exception:
            return 'ERROR: Arguments must be hexadecimal strings of even length'
        return util.hash_to_address(version, hash)

    def q_hashpubkey(abe, page, chain):
        """shows the 160-bit hash of the given public key."""
        pubkey = wsgiref.util.shift_path_info(page['env'])
        if pubkey is None:
            return \
                "Returns the 160-bit hash of PUBKEY.\n" \
                "For example, the Bitcoin genesis block's output public key," \
                " seen in its transaction output scriptPubKey, starts with\n" \
                "04678afdb0fe..., and its hash is" \
                " 62E907B15CBF27D5425399EBF6F0FB50EBB88F18, corresponding" \
                " to address 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa.\n" \
                "/q/hashpubkey/PUBKEY\n"
        try:
            pubkey = pubkey.decode('hex')
        except Exception:
            return 'ERROR: invalid hexadecimal byte string.'
        return util.pubkey_to_hash(pubkey).encode('hex').upper()

    def q_nethash(abe, page, chain):

            return 'Shows statistics every INTERVAL blocks.\n' \
                'Negative values count back from the last block.\n' \
                '/chain/CHAIN/q/nethash[/INTERVAL[/START[/STOP]]]\n'

        interval = path_info_int(page, 144)
        start = path_info_int(page, 0)
        stop = path_info_int(page, None)

        if stop == 0:
            stop = None

        if interval < 0 and start != 0:
            return 'ERROR: Negative INTERVAL requires 0 START.'

        if interval < 0 or start < 0 or (stop is not None and stop < 0):
            count = abe.get_max_block_height(chain)
            if start < 0:
                start += count
            if stop is not None and stop < 0:
                stop += count
            if interval < 0:
                interval = -interval
                start = count - (count / interval) * interval

        # Select every INTERVAL blocks from START to STOP.
        # Standard SQL lacks an "every Nth row" feature, so we
        # provide it with the help of a table containing the integers.
        # We don't need all integers, only as many as rows we want to
        # fetch.  We happen to have a table with the desired integers,
        # namely chain_candidate; its block_height column covers the
        # required range without duplicates if properly constrained.
        # That is the story of the second JOIN.

        if stop is not None:
            stop_ix = (stop - start) / interval

        rows = abe.store.selectall("""
            SELECT b.block_height,
                   b.block_nTime,
                   b.block_chain_work,
                   b.block_nBits
              FROM block b
              JOIN chain_candidate cc ON (cc.block_id = b.block_id)
              JOIN chain_candidate ints ON (
                       ints.chain_id = cc.chain_id
                   AND ints.in_longest = 1
                   AND ints.block_height * ? + ? = cc.block_height)
             WHERE cc.in_longest = 1
               AND cc.chain_id = ?""" + (
                "" if stop is None else """
               AND ints.block_height <= ?""") + """
             ORDER BY cc.block_height""",
                                   (interval, start, chain.id)
                                   if stop is None else
                                   (interval, start, chain.id, stop_ix))

        for row in rows:
            height, nTime, chain_work, nBits = row
            nTime            = float(nTime)
            nBits            = int(nBits)
            target           = util.calculate_target(nBits)
            difficulty       = util.target_to_difficulty(target)
            work             = util.target_to_work(target)
            chain_work       = abe.store.binout_int(chain_work) - work

            if row is not rows[0] or fmt == "svg":
                height           = int(height)
                interval_work    = chain_work - prev_chain_work
                avg_target       = util.work_to_target(
                    interval_work / float(interval))
                #if avg_target == target - 1:
                #    avg_target = target
                interval_seconds = nTime - prev_nTime
                if interval_seconds <= 0:
                    nethash = 'Infinity'
                else:
                    nethash = "%.0f" % (interval_work / interval_seconds,)

                if fmt == "csv":
                    ret += "%d,%d,%d,%d,%.3f,%d,%.0f,%s\n" % (
                        height, nTime, target, avg_target, difficulty, work,
                        interval_seconds / interval, nethash)

                elif fmt in ("json", "jsonp"):
                    ret.append([
                            height, int(nTime), target, avg_target,
                            difficulty, work, chain_work, nethash])

                elif fmt == "svg":
                    ret += '<abe:nethash t="%d" d="%d"' \
                        ' w="%d"/>\n' % (nTime, work, interval_work)

            prev_nTime, prev_chain_work = nTime, chain_work


    def q_totalbc(abe, page, chain):
        """shows the amount of currency ever mined."""
        if chain is None:
            return 'Shows the amount of currency ever mined.\n' \
                'This differs from the amount in circulation when' \
                ' coins are destroyed, as happens frequently in Namecoin.\n' \
                'Unlike http://blockexplorer.com/q/totalbc, this does not' \
                ' support future block numbers, and it returns a sum of' \
                ' observed generations rather than a calculated value.\n' \
                '/chain/CHAIN/q/totalbc[/HEIGHT]\n'
        height = path_info_uint(page, None)
        if height is None:
            row = abe.store.selectrow("""
                SELECT b.block_total_satoshis
                  FROM chain c
                  LEFT JOIN block b ON (c.chain_last_block_id = b.block_id)
        else:
            row = abe.store.selectrow("""
                SELECT b.block_total_satoshis
                  FROM chain_candidate cc
                  LEFT JOIN block b ON (b.block_id = cc.block_id)
                 WHERE cc.block_height = ?
                   AND cc.in_longest = 1
            """, (height))

        return format_satoshis(row[0], chain) if row else 0

    def q_getreceivedbyaddress(abe, page, chain):
        """shows the amount ever received by a given address."""
        addr = wsgiref.util.shift_path_info(page['env'])
        if chain is None or addr is None:
            return 'returns amount of money received by given address (not balance, sends are not subtracted)\n' \
                '/chain/CHAIN/q/getreceivedbyaddress/ADDRESS\n'

        if not util.possible_address(addr):
            return 'ERROR: address invalid'

        version, hash = util.decode_address(addr)
        return format_satoshis(abe.store.get_received(chain.id, hash), chain)

    def q_getsentbyaddress(abe, page, chain):
        """shows the amount ever sent from a given address."""
        addr = wsgiref.util.shift_path_info(page['env'])
        if chain is None or addr is None:
            return 'returns amount of money sent from given address\n' \
                '/chain/CHAIN/q/getsentbyaddress/ADDRESS\n'

        if not util.possible_address(addr):
            return 'ERROR: address invalid'

        version, hash = util.decode_address(addr)
        return format_satoshis(abe.store.get_sent(chain.id, hash), chain)


    def q_addressbalance(abe, page, chain):
        """amount ever received minus amount ever sent by a given address."""
        addr = wsgiref.util.shift_path_info(page['env'])
        if chain is None or addr is None:
            return 'returns amount of money at the given address\n' \
                '/chain/CHAIN/q/addressbalance/ADDRESS\n'

        if not util.possible_address(addr):
            return 'ERROR: address invalid'

        version, hash = util.decode_address(addr)
        total = abe.store.get_balance(chain.id, hash)

        return ("ERROR: please try again" if total is None else
                format_satoshis(total, chain))


    def q_addr(abe, page, chain):
        """returns the full address having the given firstbits."""
        if not abe.store.use_firstbits:
            raise PageNotFound()

        fb = wsgiref.util.shift_path_info(page['env'])
        if fb is None:
            return 'Shows the address identified by FIRSTBITS:' \
                ' the first address in CHAIN to start with FIRSTBITS,' \
                ' where the comparison is case-insensitive.\n' \
                'See http://firstbits.com/.\n' \
                'Returns the argument if none matches.\n' \
                '/chain/CHAIN/q/addr/FIRSTBITS\n' \
                '/q/addr/FIRSTBITS\n'

        return "\n".join(abe.store.firstbits_to_addresses(
                fb, chain_id = (chain and chain.id)))


def format_satoshis(satoshis, chain):
    decimals = DEFAULT_DECIMALS if chain.decimals is None else chain.decimals
    coin = 10 ** decimals
    satoshis = int(satoshis)
    integer = satoshis / coin
    frac = satoshis % coin
    return (str(integer) +
            ('.' + (('0' * decimals) + str(frac))[-decimals:])
            .rstrip('0').rstrip('.'))


def format_difficulty(diff):
    idiff = int(diff)
    ret = '.%03d' % (int(round((diff - idiff) * 1000)),)
    while idiff > 999:
        ret = (' %03d' % (idiff % 1000,)) + ret
        idiff /= 1000
    return str(idiff) + ret


def hash_to_address_link(version, hash, dotdot, truncate_to=None, text=None, checksum=None):
    if hash == DataStore.NULL_PUBKEY_HASH:
        return 'Destroyed'
    if hash is None:
        return 'UNKNOWN'
    if checksum is None:
        addr = util.hash_to_address(version, hash)
    else:
        addr = util.hash_to_address_multichain(version, hash, checksum)


def shortlink_block(link):
        data = base58.b58decode(link, None)
        # Launch background loading of transactions
        def background_catch_up():
            while True:
                time.sleep(interval)
                req = urllib2.Request(s)
        thread.start()

    def catch_up(store):
        store.catch_up_dir(dircfg)
        elif loader in ("rpc", "rpc,blkfile", "default"):
        if not store.catch_up_rpc(dircfg):
            store.catch_up_dir(dircfg)

/**
 * Sync blocks
 */
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

                # Load any data written to the last file since we checked.
                store.import_blkdat(dircfg, ds, blkfile['name'])

                # Continue with the new file.
                blkfile = next_blkfile


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

                # !IMPORTANT
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