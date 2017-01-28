#!/usr/bin/env python3

import sys
import os
import argparse
import json
import re
from pprint import pprint
import time
from bitsharesbase import transactions, operations
from bitsharesbase.account import PrivateKey, PublicKey, Address
from bitshares.storage import configStorage as config
from bitshares.bitshares import BitShares
from bitshares.amount import Amount
from bitshares.account import Account
from bitshares.market import Market
from bitshares.dex import Dex
from bitshares.price import Price, Order
from bitshares.transactionbuilder import TransactionBuilder
from prettytable import PrettyTable
import logging
from .__version__ import __VERSION__
from .ui import (
    confirm,
    print_permissions,
    get_terminal,
    pprintOperation
)
from bitshares.exceptions import AccountDoesNotExistsException


availableConfigurationKeys = [
    "default_account",
    "node",
    "rpcuser",
    "rpcpassword",
]


def main():
    global args

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Command line tool to interact with the BitShares network"
    )

    """
        Default settings for all tools
    """
    parser.add_argument(
        '--node',
        type=str,
        default=config["node"],
        help='Websocket URL for public BitShares API (default: "wss://this.uptick.rocks/")'
    )
    parser.add_argument(
        '--rpcuser',
        type=str,
        default=config["rpcuser"],
        help='Websocket user if authentication is required'
    )
    parser.add_argument(
        '--rpcpassword',
        type=str,
        default=config["rpcpassword"],
        help='Websocket password if authentication is required'
    )
    parser.add_argument(
        '--nobroadcast', '-d',
        action='store_true',
        help='Do not broadcast anything'
    )
    parser.add_argument(
        '--nowallet', '-p',
        action='store_true',
        help='Do not load the wallet'
    )
    parser.add_argument(
        '--unsigned', '-x',
        action='store_true',
        help='Do not try to sign the transaction'
    )
    parser.add_argument(
        '--expires', '-e',
        default=30,
        help='Expiration time in seconds (defaults to 30)'
    )
    parser.add_argument(
        '--verbose', '-v',
        type=int,
        default=3,
        help='Verbosity'
    )
    parser.add_argument('--version', action='version',
                        version='%(prog)s {version}'.format(version=__VERSION__))

    subparsers = parser.add_subparsers(help='sub-command help')

    """
        Command "set"
    """
    setconfig = subparsers.add_parser('set', help='Set configuration')
    setconfig.add_argument(
        'key',
        type=str,
        choices=availableConfigurationKeys,
        help='Configuration key'
    )
    setconfig.add_argument(
        'value',
        type=str,
        help='Configuration value'
    )
    setconfig.set_defaults(command="set")

    """
        Command "config"
    """
    configconfig = subparsers.add_parser('config', help='Show local configuration')
    configconfig.set_defaults(command="config")

    """
        Command "info"
    """
    parser_info = subparsers.add_parser('info', help='Show infos about uptick and BitShares')
    parser_info.set_defaults(command="info")
    parser_info.add_argument(
        'objects',
        nargs='*',
        type=str,
        help='General information about the blockchain, a block, an account name, a public key, ...'
    )

    """
        Command "changewalletpassphrase"
    """
    changepasswordconfig = subparsers.add_parser('changewalletpassphrase', help='Change wallet password')
    changepasswordconfig.set_defaults(command="changewalletpassphrase")

    """
        Command "addkey"
    """
    addkey = subparsers.add_parser('addkey', help='Add a new key to the wallet')
    addkey.add_argument(
        '--unsafe-import-key',
        nargs='*',
        type=str,
        help='private key to import into the wallet (unsafe, unless you delete your bash history)'
    )
    addkey.set_defaults(command="addkey")

    """
        Command "delkey"
    """
    delkey = subparsers.add_parser('delkey', help='Delete keys from the wallet')
    delkey.add_argument(
        'pub',
        nargs='*',
        type=str,
        help='the public key to delete from the wallet'
    )
    delkey.set_defaults(command="delkey")

    """
        Command "getkey"
    """
    getkey = subparsers.add_parser('getkey', help='Dump the privatekey of a pubkey from the wallet')
    getkey.add_argument(
        'pub',
        type=str,
        help='the public key for which to show the private key'
    )
    getkey.set_defaults(command="getkey")

    """
        Command "listkeys"
    """
    listkeys = subparsers.add_parser('listkeys', help='List available keys in your wallet')
    listkeys.set_defaults(command="listkeys")

    """
        Command "listaccounts"
    """
    listaccounts = subparsers.add_parser('listaccounts', help='List available accounts in your wallet')
    listaccounts.set_defaults(command="listaccounts")

    """
        Command "transfer"
    """
    parser_transfer = subparsers.add_parser('transfer', help='Transfer Assets on BitShares')
    parser_transfer.set_defaults(command="transfer")
    parser_transfer.add_argument(
        'to',
        type=str,
        help='Recepient'
    )
    parser_transfer.add_argument(
        'amount',
        type=float,
        help='Amount to transfer'
    )
    parser_transfer.add_argument(
        'asset',
        type=str,
        help='Asset Symbol'
    )
    parser_transfer.add_argument(
        'memo',
        type=str,
        nargs="?",
        default="",
        help='Optional memo'
    )
    parser_transfer.add_argument(
        '--account',
        type=str,
        required=False,
        default=config["default_account"],
        help='Transfer from this account'
    )

    """
        Command "balance"
    """
    parser_balance = subparsers.add_parser('balance', help='Show the balance of one more more accounts')
    parser_balance.set_defaults(command="balance")
    parser_balance.add_argument(
        'account',
        type=str,
        nargs="*",
        default=config["default_account"],
        help='balance of these account (multiple accounts allowed)'
    )

    """
        Command "history"
    """
    parser_history = subparsers.add_parser('history', help='Show the history of an account')
    parser_history.set_defaults(command="history")
    parser_history.add_argument(
        'account',
        type=str,
        nargs="?",
        default=config["default_account"],
        help='History of this account'
    )
    parser_history.add_argument(
        '--limit',
        type=int,
        default=config["limit"] or 15,
        help='Limit number of entries'
    )
    parser_history.add_argument(
        '--memos',
        action='store_true',
        help='Show (decode) memos'
    )
    parser_history.add_argument(
        '--csv',
        action='store_true',
        help='Output in CSV format'
    )
    parser_history.add_argument(
        '--types',
        type=str,
        nargs="*",
        default=[],
        help='Show only these operation types'
    )
    parser_history.add_argument(
        '--exclude_types',
        type=str,
        nargs="*",
        default=[],
        help='Do not show operations of this type'
    )

    """
        Command "permissions"
    """
    parser_permissions = subparsers.add_parser('permissions', help='Show permissions of an account')
    parser_permissions.set_defaults(command="permissions")
    parser_permissions.add_argument(
        'account',
        type=str,
        nargs="?",
        default=config["default_account"],
        help='Account to show permissions for'
    )

    """
        Command "allow"
    """
    parser_allow = subparsers.add_parser('allow', help='Allow an account/key to interact with your account')
    parser_allow.set_defaults(command="allow")
    parser_allow.add_argument(
        '--account',
        type=str,
        nargs="?",
        default=config["default_account"],
        help='The account to allow action for'
    )
    parser_allow.add_argument(
        'foreign_account',
        type=str,
        nargs="?",
        help='The account or key that will be allowed to interact as your account'
    )
    parser_allow.add_argument(
        '--permission',
        type=str,
        default="active",
        choices=["owner", "active"],
        help=('The permission to grant (defaults to "active")')
    )
    parser_allow.add_argument(
        '--weight',
        type=int,
        default=None,
        help=('The weight to use instead of the (full) threshold. '
              'If the weight is smaller than the threshold, '
              'additional signatures are required')
    )
    parser_allow.add_argument(
        '--threshold',
        type=int,
        default=None,
        help=('The permission\'s threshold that needs to be reached '
              'by signatures to be able to interact')
    )

    """
        Command "disallow"
    """
    parser_disallow = subparsers.add_parser('disallow', help='Remove allowance an account/key to interact with your account')
    parser_disallow.set_defaults(command="disallow")
    parser_disallow.add_argument(
        '--account',
        type=str,
        nargs="?",
        default=config["default_account"],
        help='The account to disallow action for'
    )
    parser_disallow.add_argument(
        'foreign_account',
        type=str,
        help='The account or key whose allowance to interact as your account will be removed'
    )
    parser_disallow.add_argument(
        '--permission',
        type=str,
        default="active",
        choices=["owner", "active"],
        help=('The permission to remove (defaults to "active")')
    )
    parser_disallow.add_argument(
        '--threshold',
        type=int,
        default=None,
        help=('The permission\'s threshold that needs to be reached '
              'by signatures to be able to interact')
    )

    """
        Command "newaccount"
    """
    parser_newaccount = subparsers.add_parser('newaccount', help='Create a new account')
    parser_newaccount.set_defaults(command="newaccount")
    parser_newaccount.add_argument(
        'accountname',
        type=str,
        help='New account name'
    )
    parser_newaccount.add_argument(
        '--account',
        type=str,
        required=False,
        default=config["default_account"],
        help='Account that pays the fee'
    )

    """
        Command "importaccount"
    """
    parser_importaccount = subparsers.add_parser('importaccount', help='Import an account using a passphrase')
    parser_importaccount.set_defaults(command="importaccount")
    parser_importaccount.add_argument(
        'account',
        type=str,
        help='Account name'
    )
    parser_importaccount.add_argument(
        '--roles',
        type=str,
        nargs="*",
        default=["active", "memo"],  # no owner
        help='Import specified keys (owner, active, memo)'
    )

    """
        Command "updateMemoKey"
    """
    parser_updateMemoKey = subparsers.add_parser('updatememokey', help='Update an account\'s memo key')
    parser_updateMemoKey.set_defaults(command="updatememokey")
    parser_updateMemoKey.add_argument(
        '--account',
        type=str,
        nargs="?",
        default=config["default_account"],
        help='The account to updateMemoKey action for'
    )
    parser_updateMemoKey.add_argument(
        '--key',
        type=str,
        default=None,
        help='The new memo key'
    )

    """
        Command "approvewitness"
    """
    parser_approvewitness = subparsers.add_parser('approvewitness', help='Approve a witnesses')
    parser_approvewitness.set_defaults(command="approvewitness")
    parser_approvewitness.add_argument(
        'witness',
        type=str,
        help='Witness to approve'
    )
    parser_approvewitness.add_argument(
        '--account',
        type=str,
        required=False,
        default=config["default_account"],
        help='Your account'
    )

    """
        Command "disapprovewitness"
    """
    parser_disapprovewitness = subparsers.add_parser('disapprovewitness', help='Disapprove a witnesses')
    parser_disapprovewitness.set_defaults(command="disapprovewitness")
    parser_disapprovewitness.add_argument(
        'witness',
        type=str,
        help='Witness to disapprove'
    )
    parser_disapprovewitness.add_argument(
        '--account',
        type=str,
        required=False,
        default=config["default_account"],
        help='Your account'
    )

    """
        Command "sign"
    """
    parser_sign = subparsers.add_parser('sign', help='Sign a provided transaction with available and required keys')
    parser_sign.set_defaults(command="sign")
    parser_sign.add_argument(
        '--file',
        type=str,
        required=False,
        help='Load transaction from file. If "-", read from stdin (defaults to "-")'
    )

    """
        Command "broadcast"
    """
    parser_broadcast = subparsers.add_parser('broadcast', help='broadcast a signed transaction')
    parser_broadcast.set_defaults(command="broadcast")
    parser_broadcast.add_argument(
        '--file',
        type=str,
        required=False,
        help='Load transaction from file. If "-", read from stdin (defaults to "-")'
    )

    """
        Command "orderbook"
    """
    orderbook = subparsers.add_parser('orderbook', help='Obtain orderbook of the internal market')
    orderbook.set_defaults(command="orderbook")
    orderbook.add_argument(
        'market',
        help="Market to obtain orderbook for (e.g. BTS:USD)"
    )

    orderbook.add_argument(
        '--chart',
        action='store_true',
        help="Enable charting (requires matplotlib)"
    )

    """
        Command "buy"
    """
    parser_buy = subparsers.add_parser('buy', help='Buy an Asset from the internal market')
    parser_buy.set_defaults(command="buy")
    parser_buy.add_argument(
        'buy_amount',
        type=float,
        help='Amount to buy'
    )
    parser_buy.add_argument(
        'buy_asset',
        type=str,
        help='Asset to buy'
    )
    parser_buy.add_argument(
        'price',
        type=float,
        help='Limit buy price denoted in SELLASSET/BUYASSET'
    )
    parser_buy.add_argument(
        'sell_asset',
        type=str,
        help='Asset to sell'
    )
    parser_buy.add_argument(
        '--account',
        type=str,
        required=False,
        default=config["default_account"],
        help='Buy with this account (defaults to "default_account")'
    )

    """
        Command "sell"
    """
    parser_sell = subparsers.add_parser('sell', help='Sell an Asset from the internal market')
    parser_sell.set_defaults(command="sell")
    parser_sell.add_argument(
        'sell_amount',
        type=float,
        help='Amount to sell'
    )
    parser_sell.add_argument(
        'sell_asset',
        type=str,
        help='Asset to sell'
    )
    parser_sell.add_argument(
        'price',
        type=float,
        help='Limit sell price denoted in SELLASSET/sellASSET'
    )
    parser_sell.add_argument(
        'buy_asset',
        type=str,
        help='Asset to buy'
    )
    parser_sell.add_argument(
        '--account',
        type=str,
        required=False,
        default=config["default_account"],
        help='sell with this account (defaults to "default_account")'
    )

    """
        Command "openorders"
    """
    parser_openorders = subparsers.add_parser('openorders', help='Open Orders of an account')
    parser_openorders.set_defaults(command="openorders")
    parser_openorders.add_argument(
        'account',
        type=str,
        default=config["default_account"],
        nargs='?',
        help='Account to list open orders for'
    )

    """
        Parse Arguments
    """
    args = parser.parse_args()

    # Logging
    log = logging.getLogger(__name__)
    verbosity = ["critical",
                 "error",
                 "warn",
                 "info",
                 "debug"][int(min(args.verbose, 4))]
    log.setLevel(getattr(logging, verbosity.upper()))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, verbosity.upper()))
    ch.setFormatter(formatter)
    log.addHandler(ch)

    # GrapheneAPI logging
    if args.verbose > 4:
        verbosity = ["critical",
                     "error",
                     "warn",
                     "info",
                     "debug"][int(min((args.verbose - 4), 4))]
        gphlog = logging.getLogger("graphenebase")
        gphlog.setLevel(getattr(logging, verbosity.upper()))
        gphlog.addHandler(ch)
    if args.verbose > 8:
        verbosity = ["critical",
                     "error",
                     "warn",
                     "info",
                     "debug"][int(min((args.verbose - 8), 4))]
        gphlog = logging.getLogger("grapheneapi")
        gphlog.setLevel(getattr(logging, verbosity.upper()))
        gphlog.addHandler(ch)

    if not hasattr(args, "command"):
        parser.print_help()
        sys.exit(2)

    # We don't require RPC for these commands
    rpc_not_required = [
        "set",
        "config",
        ""]
    if args.command not in rpc_not_required and args.command:
        options = {
            "node": args.node,
            "rpcuser": args.rpcuser,
            "rpcpassword": args.rpcpassword,
            "nobroadcast": args.nobroadcast,
            "unsigned": args.unsigned,
            "expires": args.expires
        }

        # preload wallet with empty keys
        if args.nowallet:
            options.update({"wif": []})

        # Signing only requires the wallet, no connection
        # essential for offline/coldstorage signing
        if args.command == "sign":
            options.update({"offline": True})

        bitshares = BitShares(**options)

    if args.command == "set":
        if (args.key == "default_account" and
                args.value[0] == "@"):
            args.value = args.value[1:]
        config[args.key] = args.value

    elif args.command == "config":
        t = PrettyTable(["Key", "Value"])
        t.align = "l"
        for key in config:
            if key in availableConfigurationKeys:  # hide internal config data
                t.add_row([key, config[key]])
        print(t)

    elif args.command == "info":
        if not args.objects:
            t = PrettyTable(["Key", "Value"])
            t.align = "l"
            info = bitshares.rpc.get_dynamic_global_properties()
            for key in info:
                t.add_row([key, info[key]])
            print(t.get_string(sortby="Key"))

        for obj in args.objects:
            # Block
            if re.match("^[0-9]*$", obj):
                block = bitshares.rpc.get_block(obj)
                if block:
                    t = PrettyTable(["Key", "Value"])
                    t.align = "l"
                    for key in sorted(block):
                        value = block[key]
                        if key == "transactions":
                            value = json.dumps(value, indent=4)
                        t.add_row([key, value])
                    print(t)
                else:
                    print("Block number %s unknown" % obj)
            # Account name
            elif re.match("^[a-zA-Z0-9\._]{2,64}$", obj):
                account = bitshares.rpc.get_account(obj)
                if account:
                    t = PrettyTable(["Key", "Value"])
                    t.align = "l"
                    for key in sorted(account):
                        value = account[key]
                        if key in ["active", "owner", "options"]:
                            value = json.dumps(value, indent=4)
                        t.add_row([key, value])
                    print(t)
                else:
                    print("Account %s unknown" % obj)
            # Public Key
            elif re.match("^BTS.{48,55}$", obj):
                account = bitshares.wallet.getAccountFromPublicKey(obj)
                if account:
                    t = PrettyTable(["Account"])
                    t.align = "l"
                    t.add_row(account)
                    print(t)
                else:
                    print("Public Key not known" % obj)
            else:
                print("Couldn't identify object to read")

    elif args.command == "changewalletpassphrase":
        bitshares.wallet.changePassphrase()

    elif args.command == "addkey":
        if args.unsafe_import_key:
            for key in args.unsafe_import_key:
                try:
                    bitshares.wallet.addPrivateKey(key)
                except Exception as e:
                    print(str(e))
        else:
            import getpass
            while True:
                wifkey = getpass.getpass('Private Key (wif) [Enter to quit]:')
                if not wifkey:
                    break
                try:
                    bitshares.wallet.addPrivateKey(wifkey)
                except Exception as e:
                    print(str(e))
                    continue

                installedKeys = bitshares.wallet.getPublicKeys()
                if len(installedKeys) == 1:
                    name = bitshares.wallet.getAccountFromPublicKey(installedKeys[0])
                    account = Account(name)
                    print("=" * 30)
                    print("Setting new default user: %s" % account["name"])
                    print()
                    print("You can change these settings with:")
                    print("    uptick set default_account <account>")
                    print("=" * 30)
                    config["default_account"] = account["name"]

    elif args.command == "delkey":
        if confirm(
            "Are you sure you want to delete keys from your wallet?\n"
            "This step is IRREVERSIBLE! If you don't have a backup, "
            "You may lose access to your account!"
        ):
            for pub in args.pub:
                bitshares.wallet.removePrivateKeyFromPublicKey(pub)

    elif args.command == "getkey":
        print(bitshares.wallet.getPrivateKeyForPublicKey(args.pub))

    elif args.command == "listkeys":
        t = PrettyTable(["Available Key"])
        t.align = "l"
        for key in bitshares.wallet.getPublicKeys():
            t.add_row([key])
        print(t)

    elif args.command == "listaccounts":
        t = PrettyTable(["Name", "Type", "Available Key"])
        t.align = "l"
        for account in bitshares.wallet.getAccounts():
            t.add_row([
                account["name"] or "n/a",
                account["type"] or "n/a",
                account["pubkey"]
            ])
        print(t)

    # Actual BitShares Related sub commands
    ##################################################################
    elif args.command == "transfer":
        pprint(bitshares.transfer(
            args.to,
            args.amount,
            args.asset,
            memo=args.memo,
            account=args.account
        ))

    elif args.command == "balance":
        t = PrettyTable(["Account", "Amount", "Asset"])
        t.align = "r"
        for a in args.account.split(" "):
            account = Account(a)
            for b in account.balances:
                t.add_row([
                    str(a),
                    b.amount,
                    b.symbol,
                ])
        print(t)

    elif args.command == "permissions":
        account = bitshares.rpc.get_account(args.account)
        print_permissions(account)

    elif args.command == "allow":
        if not args.foreign_account:
            from bitsharesbase.account import PasswordKey
            pwd = get_terminal(text="Password for Key Derivation: ", confirm=True)
            args.foreign_account = format(PasswordKey(args.account, pwd, args.permission).get_public(), "STM")
        pprint(bitshares.allow(
            args.foreign_account,
            weight=args.weight,
            account=args.account,
            permission=args.permission,
            threshold=args.threshold
        ))

    elif args.command == "disallow":
        pprint(bitshares.disallow(
            args.foreign_account,
            account=args.account,
            permission=args.permission,
            threshold=args.threshold
        ))

    elif args.command == "sign":
        if args.file and args.file != "-":
            if not os.path.isfile(args.file):
                raise Exception("File %s does not exist!" % args.file)
            with open(args.file) as fp:
                tx = fp.read()
        else:
            tx = sys.stdin.read()
        tx = TransactionBuilder(eval(tx))
        tx.appendMissingSignatures()
        tx.sign()
        pprint(tx.json())

    elif args.command == "broadcast":
        if args.file and args.file != "-":
            if not os.path.isfile(args.file):
                raise Exception("File %s does not exist!" % args.file)
            with open(args.file) as fp:
                tx = fp.read()
        else:
            tx = sys.stdin.read()
        tx = TransactionBuilder(eval(tx))
        tx.broadcast()
        pprint(tx.json())

    elif args.command == "orderbook":
        market = Market(args.market, bitshares_instance=bitshares)
        orderbook = market.orderbook()
        if args.chart:
            try:
                import numpy
                import Gnuplot
                from itertools import accumulate
            except:
                print("To use --chart, you need gnuplot and gnuplot-py installed")
                sys.exit(1)
            g = Gnuplot.Gnuplot()
            g.title("DEX - {quote}:{base}".format(quote=quote, base=base))
            g.xlabel("price in %s/%s" % (base, quote))
            g.ylabel("volume")
            xbids = [x["price"] for x in orderbook["bids"]]
            ybids = list(accumulate([x["fixme"] for x in orderbook["bids"]]))
            dbids = Gnuplot.Data(xbids, ybids, with_="lines")
            xasks = [x["price"] for x in orderbook["asks"]]
            yasks = list(accumulate([x["fixme"] for x in orderbook["asks"]]))
            dasks = Gnuplot.Data(xasks, yasks, with_="lines")
            g("set terminal dumb")
            g.plot(dbids, dasks)  # write SVG data directly to stdout ...

        ta = {}
        ta["bids"] = PrettyTable([
            "quote",
            "base",
            "price"
        ])
        ta["bids"].align = "r"
        for order in orderbook["bids"]:
            ta["bids"].add_row([
                order["quote_amount"],
                order["base_amount"],
                order["price"]
            ])

        ta["asks"] = PrettyTable([
            "price",
            "base",
            "quote",
        ])
        ta["asks"].align = "r"
        ta["asks"].align["price"] = "l"
        for order in orderbook["asks"]:
            ta["asks"].add_row([
                order["price"],
                order["base_amount"],
                order["quote_amount"]
            ])

        t = PrettyTable(["bids", "asks"])
        t.add_row([str(ta["bids"]), str(ta["asks"])])
        print(t)

    elif args.command == "buy":
        amount = Amount(args.buy_amount, args.buy_asset)
        price = Price(
            args.price,
            base=args.sell_asset,
            quote=args.buy_asset
        )
        pprint(price.market.buy(
            price,
            amount,
            account=args.account
        ))

    elif args.command == "sell":
        amount = Amount(args.sell_amount, args.sell_asset)
        price = Price(
            args.price,
            quote=args.sell_asset,
            base=args.buy_asset,
        )
        pprint(price.market.sell(
            price,
            amount,
            account=args.account
        ))

    elif args.command == "openorders":
        account = Account(args.account)
        t = PrettyTable([
            "Price",
            "Quote Amount",
            "Base Amount",
        ])
        t.align = "r"
        for o in account.openorders:
            t.add_row([
                o["price"],
                o["quote_amount"],
                o["base_amount"],
            ])
        print(t)

    elif args.command == "history":
        from bitsharesbase.operations import getOperationNameForId
        header = ["#", "time (block)", "operation", "details"]
        if args.csv:
            import csv
            t = csv.writer(sys.stdout, delimiter=";")
            t.writerow(header)
        else:
            t = PrettyTable(header)
            t.align = "r"
            t.align["details"] = "l"
        if isinstance(args.account, str):
            args.account = [args.account]
        if isinstance(args.types, str):
            args.types = [args.types]

        for a in args.account:
            account = Account(a)
            for b in account.rawhistory(
                limit=args.limit,
                only_ops=args.types,
                exclude_ops=args.exclude_types
            ):
                row = [
                    b["id"].split(".")[2],
                    "%s" % (b["block_num"]),
                    "{} ({})".format(getOperationNameForId(b["op"][0]), b["op"][0]),
                    pprintOperation(b),
                ]
                if args.csv:
                    t.writerow(row)
                else:
                    t.add_row(row)
        if not args.csv:
            print(t)
    """
    elif args.command == "newaccount":
        import getpass
        while True:
            pw = getpass.getpass("New Account Passphrase: ")
            if not pw:
                print("You cannot chosen an empty password!")
                continue
            else:
                pwck = getpass.getpass(
                    "Confirm New Account Passphrase: "
                )
                if (pw == pwck):
                    break
                else:
                    print("Given Passphrases do not match!")
        pprint(bitshares.create_account(
            args.accountname,
            creator=args.account,
            password=pw,
        ))

    elif args.command == "importaccount":
        from bitsharesbase.account import PasswordKey
        import getpass
        password = getpass.getpass("Account Passphrase: ")
        account = bitshares.rpc.get_account(args.account)
        imported = False

        if "owner" in args.roles:
            owner_key = PasswordKey(args.account, password, role="owner")
            owner_pubkey = format(owner_key.get_public_key(), "STM")
            if owner_pubkey in [x[0] for x in account["owner"]["key_auths"]]:
                print("Importing owner key!")
                owner_privkey = owner_key.get_private_key()
                bitshares.wallet.addPrivateKey(owner_privkey)
                imported = True

        if "active" in args.roles:
            active_key = PasswordKey(args.account, password, role="active")
            active_pubkey = format(active_key.get_public_key(), "STM")
            if active_pubkey in [x[0] for x in account["active"]["key_auths"]]:
                print("Importing active key!")
                active_privkey = active_key.get_private_key()
                bitshares.wallet.addPrivateKey(active_privkey)
                imported = True

        if "memo" in args.roles:
            memo_key = PasswordKey(args.account, password, role="memo")
            memo_pubkey = format(memo_key.get_public_key(), "STM")
            if memo_pubkey == account["memo_key"]:
                print("Importing memo key!")
                memo_privkey = memo_key.get_private_key()
                bitshares.wallet.addPrivateKey(memo_privkey)
                imported = True

        if not imported:
            print("No matching key(s) found. Password correct?")

    elif args.command == "approvewitness":
        pprint(bitshares.approve_witness(
            args.witness,
            account=args.account
        ))

    elif args.command == "disapprovewitness":
        pprint(bitshares.disapprove_witness(
            args.witness,
            account=args.account
        ))

    else:
        print("No valid command given")
"""


args = None

if __name__ == '__main__':
    main()
