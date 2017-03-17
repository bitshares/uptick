#!/usr/bin/env python3

import sys
import os
import json
import re
from pprint import pprint
import time
from bitsharesbase import transactions, operations
from bitsharesbase.account import PrivateKey, PublicKey, Address
from bitshares.storage import configStorage as config
from bitshares.bitshares import BitShares
from bitshares.block import Block
from bitshares.amount import Amount
from bitshares.asset import Asset
from bitshares.account import Account
from bitshares.market import Market
from bitshares.dex import Dex
from bitshares.price import Price, Order
from bitshares.transactionbuilder import TransactionBuilder
from bitshares.instance import set_shared_bitshares_instance
from prettytable import PrettyTable
import logging
from .ui import (
    print_permissions,
    get_terminal,
    pprintOperation,
    print_version,
    onlineChain,
    offlineChain,
    unlockWallet
)
from bitshares.exceptions import AccountDoesNotExistsException
import click
from click_datetime import Datetime
from datetime import datetime
log = logging.getLogger(__name__)


@click.group()
@click.option(
    '--debug/--no-debug',
    default=False,
    help="Enable/Disable Debugging (no-broadcasting mode)"
)
@click.option(
    '--node',
    type=str,
    default=config["node"],
    help='Websocket URL for public BitShares API (default: "wss://this.uptick.rocks/")'
)
@click.option(
    '--rpcuser',
    type=str,
    default=config["rpcuser"],
    help='Websocket user if authentication is required'
)
@click.option(
    '--rpcpassword',
    type=str,
    default=config["rpcpassword"],
    help='Websocket password if authentication is required')
@click.option(
    '--nobroadcast/--broadcast',
    '-d',
    default=False,
    help='Do not broadcast anything')
@click.option(
    '--unsigned/--signed',
    '-x',
    default=False,
    help='Do not try to sign the transaction')
@click.option(
    '--expires',
    '-e',
    default=30,
    help='Expiration time in seconds (defaults to 30)')
@click.option(
    '--verbose',
    '-v',
    type=int,
    default=3,
    help='Verbosity (0-15)')
@click.option(
    '--version',
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Show version")
@click.pass_context
def main(ctx, **kwargs):
    ctx.obj = {}
    for k, v in kwargs.items():
        ctx.obj[k] = v


@main.command(
    help="Set configuration key/value pair"
)
@click.pass_context
@offlineChain
@click.argument(
    'key',
    type=str
)
@click.argument(
    'value',
    type=str
)
def set(ctx, key, value):
    """ Set configuration parameters
    """
    if (key == "default_account" and
            value[0] == "@"):
        value = value[1:]
    config[key] = value


@main.command(
    help="Show configuration variables"
)
def configuration():
    t = PrettyTable(["Key", "Value"])
    t.align = "l"
    for key in config:
        if key not in [
            "encrypted_master_password"
        ]:
            t.add_row([key, config[key]])
    click.echo(t)


@main.command(
    help="Change the wallet passphrase"
)
@click.pass_context
@offlineChain
@click.option(
    '--new-password',
    prompt="New Wallet Passphrase",
    hide_input=True,
    confirmation_prompt=True,
    help="New Wallet Passphrase"
)
@unlockWallet
def changewalletpassphrase(ctx, new_password):
    ctx.bitshares.wallet.changePassphrase(new_password)


@main.command(
    help="Add a private key to the wallet"
)
@click.pass_context
@onlineChain
@click.argument(
    "key",
    nargs=-1
)
@unlockWallet
def addkey(ctx, key):
    if not key:
        while True:
            key = click.prompt(
                "Private Key (wif) [Enter to quit]",
                hide_input=True,
                show_default=False,
                default="exit"
            )
            if not key or key == "exit":
                break
            try:
                ctx.bitshares.wallet.addPrivateKey(key)
            except Exception as e:
                click.echo(str(e))
                continue

        installedKeys = ctx.bitshares.wallet.getPublicKeys()
        if len(installedKeys) == 1:
            name = ctx.bitshares.wallet.getAccountFromPublicKey(installedKeys[0])
            account = Account(name, bitshares_instance=ctx.bitshares)
            click.echo("=" * 30)
            click.echo("Setting new default user: %s" % account["name"])
            click.echo()
            click.echo("You can change these settings with:")
            click.echo("    uptick set default_account <account>")
            click.echo("=" * 30)
            config["default_account"] = account["name"]


@main.command(
    help="Delete a private key from the wallet"
)
@click.pass_context
@offlineChain
@click.argument(
    "pubkeys",
    nargs=-1
)
def delkey(ctx, pubkeys):
    if not pubkeys:
        pubkeys = click.prompt("Public Keys").split(" ")
    if click.confirm(
        "Are you sure you want to delete keys from your wallet?\n"
        "This step is IRREVERSIBLE! If you don't have a backup, "
        "You may lose access to your account!"
    ):
        for pub in pubkeys:
            ctx.bitshares.wallet.removePrivateKeyFromPublicKey(pub)


@main.command(
    help="Obtain private key in WIF format"
)
@click.pass_context
@offlineChain
@click.argument(
    "pubkey",
    nargs=1
)
@unlockWallet
def getkey(ctx, pubkey):
    click.echo(ctx.bitshares.wallet.getPrivateKeyForPublicKey(pubkey))


@main.command(
    help="List all keys (for all networks)"
)
@click.pass_context
@offlineChain
def listkeys(ctx):
    t = PrettyTable(["Available Key"])
    t.align = "l"
    for key in ctx.bitshares.wallet.getPublicKeys():
        t.add_row([key])
    click.echo(t)


@main.command(
    help="List accounts (for the connected network)"
)
@click.pass_context
@onlineChain
def listaccounts(ctx):
    t = PrettyTable(["Name", "Type", "Available Key"])
    t.align = "l"
    for account in ctx.bitshares.wallet.getAccounts():
        t.add_row([
            account["name"] or "n/a",
            account["type"] or "n/a",
            account["pubkey"]
        ])
    click.echo(t)


@main.command(
    help="Obtain all kinds of information"
)
@click.pass_context
@onlineChain
@click.argument(
    'objects',
    type=str,
    nargs=-1
)
def info(ctx, objects):
    if not objects:
        t = PrettyTable(["Key", "Value"])
        t.align = "l"
        info = ctx.bitshares.rpc.get_dynamic_global_properties()
        for key in info:
            t.add_row([key, info[key]])
        click.echo(t.get_string(sortby="Key"))

    for obj in objects:
        # Block
        if re.match("^[0-9]*$", obj):
            block = Block(obj, bitshares_instance=ctx.bitshares)
            if block:
                t = PrettyTable(["Key", "Value"])
                t.align = "l"
                for key in sorted(block):
                    value = block[key]
                    if key == "transactions":
                        value = json.dumps(value, indent=4)
                    t.add_row([key, value])
                click.echo(t)
            else:
                click.echo("Block number %s unknown" % obj)
        # Object Id
        elif len(obj.split(".")) == 3:
            data = ctx.bitshares.rpc.get_object(obj)
            if data:
                t = PrettyTable(["Key", "Value"])
                t.align = "l"
                for key in sorted(data):
                    value = data[key]
                    if isinstance(value, dict):
                        value = json.dumps(value, indent=4)
                    t.add_row([key, value])
                click.echo(t)
            else:
                click.echo("Object %s unknown" % obj)

        # Asset
        elif obj.upper() == obj:
            data = Asset(obj)
            t = PrettyTable(["Key", "Value"])
            t.align = "l"
            for key in sorted(data):
                value = data[key]
                if isinstance(value, dict):
                    value = json.dumps(value, indent=4)
                t.add_row([key, value])
            click.echo(t)

        # Public Key
        elif re.match("^BTS.{48,55}$", obj):
            account = ctx.bitshares.wallet.getAccountFromPublicKey(obj)
            if account:
                t = PrettyTable(["Account"])
                t.align = "l"
                t.add_row([account])
                click.echo(t)
            else:
                click.echo("Public Key not known" % obj)

        # Account name
        elif re.match("^[a-zA-Z0-9\-\._]{2,64}$", obj):
            account = Account(obj, full=True)
            if account:
                t = PrettyTable(["Key", "Value"])
                t.align = "l"
                for key in sorted(account):
                    value = account[key]
                    if isinstance(value, dict) or isinstance(value, list):
                        value = json.dumps(value, indent=4)
                    t.add_row([key, value])
                click.echo(t)
            else:
                click.echo("Account %s unknown" % obj)
        else:
            click.echo("Couldn't identify object to read")


@main.command(
    help="Show Account balances"
)
@click.pass_context
@onlineChain
@click.argument(
    "accounts",
    nargs=-1)
def balance(ctx, accounts):
    t = PrettyTable(["Account", "Amount"])
    t.align = "r"
    for a in accounts:
        account = Account(a, bitshares_instance=ctx.bitshares)
        for b in account.balances:
            t.add_row([
                str(a),
                str(b),
            ])
    click.echo(str(t))


@main.command(
    help="Show permissions of an account"
)
@click.pass_context
@onlineChain
@click.argument(
    "account",
    nargs=1)
def permissions(ctx, account):
    print_permissions(Account(account))


@main.command(
    help="Transfer assets"
)
@click.pass_context
@onlineChain
@click.argument(
    "to",
    nargs=1,
    type=str)
@click.argument(
    "amount",
    nargs=1,
    type=float)
@click.argument(
    "asset",
    nargs=1,
    type=str)
@click.argument(
    "memo",
    required=False,
    type=str,
    default=None)
@click.option(
    "--account",
    default=config["default_account"],
    help="Account to send from"
)
@unlockWallet
def transfer(ctx, to, amount, asset, memo, account):
    pprint(ctx.bitshares.transfer(
        to,
        amount,
        asset,
        memo=memo,
        account=account
    ))


@main.command(
    help="Add a key/account to an account's permission"
)
@click.pass_context
@onlineChain
@click.argument(
    "foreign_account",
    required=False,
    type=str)
@click.option(
    "--account",
    default=config["default_account"],
    type=str,
    help="Account to be modified"
)
@click.option(
    "--permission",
    default="active",
    type=str,
    help="Permission/Role to be modified"
)
@click.option(
    "--threshold",
    type=int,
    help="Threshold for the Role"
)
@click.option(
    "--weight",
    type=int,
    help="Weight of the new key/account"
)
@unlockWallet
def allow(ctx, foreign_account, permission, weight, threshold, account):
    if not foreign_account:
        from bitsharesbase.account import PasswordKey
        pwd = click.prompt(
            "Password for Key Derivation",
            hide_input=True,
            confirmation_prompt=True
        )
        foreign_account = format(
            PasswordKey(account, pwd, permission).get_public(),
            "BTS"
        )
    pprint(ctx.bitshares.allow(
        foreign_account,
        weight=weight,
        account=account,
        permission=permission,
        threshold=threshold
    ))


@main.command(
    help="Remove a key/account from an account's permission"
)
@click.pass_context
@onlineChain
@click.argument(
    "foreign_account",
    type=str)
@click.option(
    "--account",
    default=config["default_account"],
    help="Account to be modified",
    type=str)
@click.option(
    "--permission",
    default="active",
    help="Permission/Role to be modified",
    type=str)
@click.option(
    "--threshold",
    help="Threshold for the Role",
    type=int)
@unlockWallet
def disallow(ctx, foreign_account, permission, threshold, account):
    pprint(ctx.bitshares.disallow(
        foreign_account,
        account=account,
        permission=permission,
        threshold=threshold
    ))


@main.command(
    help="Sign a json-formatted transaction"
)
@click.pass_context
@offlineChain
@click.argument(
    'filename',
    required=False,
    type=click.File('r'))
@unlockWallet
def sign(ctx, filename):
    if filename:
        tx = filename.read()
    else:
        tx = sys.stdin.read()
    tx = TransactionBuilder(eval(tx), bitshares_instance=ctx.bitshares)
    tx.appendMissingSignatures()
    tx.sign()
    pprint(tx.json())


@main.command(
    help="Broadcast a json-formatted transaction"
)
@click.pass_context
@onlineChain
@click.argument(
    'filename',
    required=False,
    type=click.File('r'))
@unlockWallet
def broadcast(ctx, filename):
    if filename:
        tx = filename.read()
    else:
        tx = sys.stdin.read()
    tx = TransactionBuilder(eval(tx), bitshares_instance=ctx.bitshares)
    tx.broadcast()
    pprint(tx.json())


@main.command(
    help="Show the orderbook of a particular market"
)
@click.pass_context
@onlineChain
@click.argument(
    'market',
    nargs=1)
def orderbook(ctx, market):
    market = Market(market, bitshares_instance=ctx.bitshares)
    orderbook = market.orderbook()
    ta = {}
    ta["bids"] = PrettyTable([
        "quote",
        "base",
        "price"
    ])
    ta["bids"].align = "r"
    for order in orderbook["bids"]:
        ta["bids"].add_row([
            str(order["quote"]),
            str(order["base"]),
            "{:f} {}/{}".format(
                order["price"],
                order["base"]["asset"]["symbol"],
                order["quote"]["asset"]["symbol"]),
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
            "{:f} {}/{}".format(
                order["price"],
                order["base"]["asset"]["symbol"],
                order["quote"]["asset"]["symbol"]),
            str(order["base"]),
            str(order["quote"])
        ])
    t = PrettyTable(["bids", "asks"])
    t.add_row([str(ta["bids"]), str(ta["asks"])])
    click.echo(t)


@main.command(
    help="Buy a specific asset at a certain rate against a base asset"
)
@click.pass_context
@onlineChain
@click.argument(
    "buy_amount",
    type=float)
@click.argument(
    "buy_asset",
    type=str)
@click.argument(
    "price",
    type=float)
@click.argument(
    "sell_asset",
    type=str)
@click.option(
    "--account",
    default=config["default_account"],
    type=str,
    help="Account to use for this action"
)
@unlockWallet
def buy(ctx, buy_amount, buy_asset, price, sell_asset, account):
    amount = Amount(buy_amount, buy_asset)
    price = Price(
        price,
        base=sell_asset,
        quote=buy_asset,
        bitshares_instance=ctx.bitshares
    )
    pprint(price.market.buy(
        price,
        amount,
        account=account,
    ))


@main.command(
    help="Sell a specific asset at a certain rate against a base asset"
)
@click.pass_context
@onlineChain
@click.argument(
    "sell_amount",
    type=float)
@click.argument(
    "sell_asset",
    type=str)
@click.argument(
    "price",
    type=float)
@click.argument(
    "buy_asset",
    type=str)
@click.option(
    "--account",
    default=config["default_account"],
    help="Account to use for this action",
    type=str)
@unlockWallet
def sell(ctx, sell_amount, sell_asset, price, buy_asset, account):
    amount = Amount(sell_amount, sell_asset)
    price = Price(
        price,
        quote=sell_asset,
        base=buy_asset,
        bitshares_instance=ctx.bitshares
    )
    pprint(price.market.sell(
        price,
        amount,
        account=account
    ))


@main.command(
    help="List open orders of an account"
)
@click.pass_context
@onlineChain
@click.argument(
    "account",
    type=str)
def openorders(ctx, account):
    account = Account(
        account or config["default_account"],
        bitshares_instance=ctx.bitshares
    )
    t = PrettyTable([
        "Price",
        "Quote",
        "Base",
        "ID"
    ])
    t.align = "r"
    for o in account.openorders:
        t.add_row([
            "{:f} {}/{}".format(
                o["price"],
                o["base"]["asset"]["symbol"],
                o["quote"]["asset"]["symbol"]),
            str(o["quote"]),
            str(o["base"]),
            o["id"]])
    click.echo(t)


@main.command(
    help="Cancel one or multiple orders"
)
@click.pass_context
@onlineChain
@click.argument(
    "orders",
    type=str,
    nargs=-1
)
@unlockWallet
def cancel(ctx, orders):
    click.echo(ctx.bitshares.cancel(orders))


@main.command(
    help="Show history of an account"
)
@click.pass_context
@onlineChain
@click.argument(
    "account",
    nargs=-1)
@click.option(
    "--csv/--table",
    help="Show output as csv or table",
    default=False)
@click.option(
    "--type",
    type=str,
    help="Only show operations of this type",
    multiple=True)
@click.option(
    "--exclude",
    type=str,
    help="Exclude certain types",
    multiple=True)
@click.option(
    "--limit",
    type=int,
    help="Limit number of elements",
    default=15)
def history(ctx, account, limit, type, csv, exclude):
    from bitsharesbase.operations import getOperationNameForId
    header = ["#", "time (block)", "operation", "details"]
    if csv:
        import csv
        t = csv.writer(sys.stdout, delimiter=";")
        t.writerow(header)
    else:
        t = PrettyTable(header)
        t.align = "r"
        t.align["details"] = "l"

    for a in account:
        account = Account(a, bitshares_instance=ctx.bitshares)
        for b in account.history(
            limit=limit,
            only_ops=type,
            exclude_ops=exclude
        ):
            row = [
                b["id"].split(".")[2],
                "%s" % (b["block_num"]),
                "{} ({})".format(getOperationNameForId(b["op"][0]), b["op"][0]),
                pprintOperation(b),
            ]
            if csv:
                t.writerow(row)
            else:
                t.add_row(row)
    if not csv:
        click.echo(t)


@main.command(
    help="List trades in a market"
)
@click.pass_context
@onlineChain
@click.argument(
    'market',
    nargs=1)
@click.option(
    '--limit',
    type=int,
    help="Limit number of elements",
    default=10)   # fixme add start and stop time
@click.option(
    '--start',
    help="Start datetime '%Y-%m-%d %H:%M:%S'",
    type=Datetime(format='%Y-%m-%d %H:%M:%S'))
@click.option(
    '--stop',
    type=Datetime(format='%Y-%m-%d %H:%M:%S'),
    help="Stop datetime '%Y-%m-%d %H:%M:%S'",
    default=datetime.utcnow())
def trades(ctx, market, limit, start, stop):
    market = Market(market, bitshares_instance=ctx.bitshares)
    t = PrettyTable(["time", "quote", "base", "price"])
    t.align = 'r'
    for trade in market.trades(limit, start=start, stop=stop):
        t.add_row([
            str(trade["time"]),
            str(trade["quote"]),
            str(trade["base"]),
            "{:f} {}/{}".format(
                trade["price"],
                trade["base"]["asset"]["symbol"],
                trade["quote"]["asset"]["symbol"]),
        ])
    click.echo(str(t))


@main.command(
    help="Obtain a random private/public key pair"
)
@click.option(
    '--prefix',
    type=str,
    default="BTS",
    help="The refix to use"
)
@click.option(
    '--num',
    type=int,
    default=1,
    help="The number of keys to derive"
)
def randomwif(prefix, num):
    t = PrettyTable(["wif", "pubkey"])
    for n in range(0, num):
        wif = PrivateKey()
        t.add_row([
            str(wif),
            format(wif.pubkey, prefix)
        ])
    click.echo(str(t))


@main.command(
    help="Approve witness(es)"
)
@click.pass_context
@onlineChain
@click.argument(
    'witnesses',
    nargs=-1)
@click.option(
    "--account",
    default=config["default_account"],
    help="Account that takes this action",
    type=str)
@unlockWallet
def approvewitness(ctx, witnesses, account):
    pprint(ctx.bitshares.approvewitness(
        witnesses,
        account=account
    ))


@main.command(
    help="Disapprove witness(es)"
)
@click.pass_context
@onlineChain
@click.argument(
    'witnesses',
    nargs=-1)
@click.option(
    "--account",
    help="Account that takes this action",
    default=config["default_account"],
    type=str)
@unlockWallet
def disapprovewitness(ctx, witnesses, account):
    pprint(ctx.bitshares.disapprovewitness(
        witnesses,
        account=account
    ))


@main.command()
@click.pass_context
@onlineChain
@click.option(
    "--account",
    default=config["default_account"],
    type=str)
@click.option(
    "--to",
    default="faucet",
    type=str)
@click.option(
    "--ops",
    default=1,
    type=int)
@click.option(
    "--txs",
    default=-1,
    type=int)
@unlockWallet
def flood(ctx, account, ops, txs, to):
    from bitsharesbase.operations import Transfer
    from bitshares.transactionbuilder import TransactionBuilder
    assert ctx.bitshares.rpc.chain_params["prefix"] == "TEST", "Flooding only on the testnet. Please switch the API to node testnet.bitshares.eu"
    account = Account(account, bitshares_instance=ctx.bitshares)
    to_account = Account(to, bitshares_instance=ctx.bitshares)
    tx = TransactionBuilder(bitshares_instance=ctx.bitshares)

    txcnt = 0
    while txcnt < txs or txs < 0:
        txcnt += 1
        for j in range(0, ops):
            tx.appendOps(Transfer(**{
                "fee": {"amount": 0, "asset_id": "1.3.0"},
                "from": account["id"],
                "to": to_account["id"],
                "amount": {
                    "amount": 1,
                    "asset_id": "1.3.0"
                },
                "memo": None
            }))
        tx.appendSigner(account, "active")
        tx.broadcast()
        click.echo(tx["signatures"])


if __name__ == '__main__':
    main()
