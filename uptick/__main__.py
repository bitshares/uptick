#!/usr/bin/env python3

import sys
import os
import json
import re
import math
import time
from pprint import pprint
from tqdm import tqdm
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
from bitshares.witness import Witness, Witnesses
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
from datetime import datetime, timedelta
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


@main.command()
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


@main.command()
def configuration():
    """ Show configuration variables
    """
    t = PrettyTable(["Key", "Value"])
    t.align = "l"
    for key in config:
        if key not in [
            "encrypted_master_password"
        ]:
            t.add_row([key, config[key]])
    click.echo(t)


@main.command()
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
    """ Change the wallet passphrase
    """
    ctx.bitshares.wallet.changePassphrase(new_password)


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    "key",
    nargs=-1
)
@unlockWallet
def addkey(ctx, key):
    """ Add a private key to the wallet
    """
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
    else:
        for k in key:
            try:
                ctx.bitshares.wallet.addPrivateKey(k)
            except Exception as e:
                click.echo(str(e))

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


@main.command()
@click.pass_context
@offlineChain
@click.argument(
    "pubkeys",
    nargs=-1
)
def delkey(ctx, pubkeys):
    """ Delete a private key from the wallet
    """
    if not pubkeys:
        pubkeys = click.prompt("Public Keys").split(" ")
    if click.confirm(
        "Are you sure you want to delete keys from your wallet?\n"
        "This step is IRREVERSIBLE! If you don't have a backup, "
        "You may lose access to your account!"
    ):
        for pub in pubkeys:
            ctx.bitshares.wallet.removePrivateKeyFromPublicKey(pub)


@main.command()
@click.pass_context
@offlineChain
@click.argument(
    "pubkey",
    nargs=1
)
@unlockWallet
def getkey(ctx, pubkey):
    """ Obtain private key in WIF format
    """
    click.echo(ctx.bitshares.wallet.getPrivateKeyForPublicKey(pubkey))


@main.command()
@click.pass_context
@offlineChain
def listkeys(ctx):
    """ List all keys (for all networks)
    """
    t = PrettyTable(["Available Key"])
    t.align = "l"
    for key in ctx.bitshares.wallet.getPublicKeys():
        t.add_row([key])
    click.echo(t)


@main.command()
@click.pass_context
@onlineChain
def listaccounts(ctx):
    """ List accounts (for the connected network)
    """
    t = PrettyTable(["Name", "Type", "Available Key"])
    t.align = "l"
    for account in ctx.bitshares.wallet.getAccounts():
        t.add_row([
            account["name"] or "n/a",
            account["type"] or "n/a",
            account["pubkey"]
        ])
    click.echo(t)


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    'objects',
    type=str,
    nargs=-1
)
def info(ctx, objects):
    """ Obtain all kinds of information
    """
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
                    if isinstance(value, dict) or isinstance(value, list):
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


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    "accounts",
    nargs=-1)
def balance(ctx, accounts):
    """ Show Account balances
    """
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


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    "account",
    nargs=1)
def permissions(ctx, account):
    """ Show permissions of an account
    """
    print_permissions(Account(account))


@main.command()
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
    """ Transfer assets
    """
    pprint(ctx.bitshares.transfer(
        to,
        amount,
        asset,
        memo=memo,
        account=account
    ))


@main.command()
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
    """ Add a key/account to an account's permission
    """
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


@main.command()
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
    """ Remove a key/account from an account's permission
    """
    pprint(ctx.bitshares.disallow(
        foreign_account,
        account=account,
        permission=permission,
        threshold=threshold
    ))


@main.command()
@click.pass_context
@offlineChain
@click.argument(
    'filename',
    required=False,
    type=click.File('r'))
@unlockWallet
def sign(ctx, filename):
    """ Sign a json-formatted transaction
    """
    if filename:
        tx = filename.read()
    else:
        tx = sys.stdin.read()
    tx = TransactionBuilder(eval(tx), bitshares_instance=ctx.bitshares)
    tx.appendMissingSignatures()
    tx.sign()
    pprint(tx.json())


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    'filename',
    required=False,
    type=click.File('r'))
@unlockWallet
def broadcast(ctx, filename):
    """ Broadcast a json-formatted transaction
    """
    if filename:
        tx = filename.read()
    else:
        tx = sys.stdin.read()
    tx = TransactionBuilder(eval(tx), bitshares_instance=ctx.bitshares)
    tx.broadcast()
    pprint(tx.json())


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    'market',
    nargs=1)
def orderbook(ctx, market):
    """ Show the orderbook of a particular market
    """
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


@main.command()
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
    """ Buy a specific asset at a certain rate against a base asset
    """
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


@main.command()
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
    """ Sell a specific asset at a certain rate against a base asset
    """
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


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    "account",
    type=str)
def openorders(ctx, account):
    """ List open orders of an account
    """
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


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    "orders",
    type=str,
    nargs=-1
)
@unlockWallet
def cancel(ctx, orders):
    """ Cancel one or multiple orders
    """
    click.echo(ctx.bitshares.cancel(orders))


@main.command()
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
@click.option('--raw/--no-raw', default=False)
def history(ctx, account, limit, type, csv, exclude, raw):
    """ Show history of an account
    """
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
                pprintOperation(b) if not raw else json.dumps(b, indent=4),
            ]
            if csv:
                t.writerow(row)
            else:
                t.add_row(row)
    if not csv:
        click.echo(t)


@main.command()
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
    """ List trades in a market
    """
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


@main.command()
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
    """ Obtain a random private/public key pair
    """
    t = PrettyTable(["wif", "pubkey"])
    for n in range(0, num):
        wif = PrivateKey()
        t.add_row([
            str(wif),
            format(wif.pubkey, prefix)
        ])
    click.echo(str(t))


@main.command()
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
    """ Approve witness(es)
    """
    pprint(ctx.bitshares.approvewitness(
        witnesses,
        account=account
    ))


@main.command()
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
    """ Disapprove witness(es)
    """
    pprint(ctx.bitshares.disapprovewitness(
        witnesses,
        account=account
    ))


@main.command()
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
def approvecommittee(ctx, witnesses, account):
    """ Approve committee member(s)
    """
    pprint(ctx.bitshares.approvecommittee(
        witnesses,
        account=account
    ))


@main.command()
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
def disapprovecommittee(ctx, witnesses, account):
    """ Disapprove committee member(s)
    """
    pprint(ctx.bitshares.disapprovecommittee(
        witnesses,
        account=account
    ))


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    'proposal',
    nargs=1)
@click.option(
    "--account",
    help="Account that takes this action",
    default=config["default_account"],
    type=str)
@unlockWallet
def disapproveproposal(ctx, proposal, account):
    """ Disapprove a proposal
    """
    pprint(ctx.bitshares.disapproveproposal(
        proposal,
        account=account
    ))


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    'proposal',
    nargs=1)
@click.option(
    "--account",
    help="Account that takes this action",
    default=config["default_account"],
    type=str)
@unlockWallet
def approveproposal(ctx, proposal, account):
    """ Approve a proposal
    """
    pprint(ctx.bitshares.approveproposal(
        proposal,
        account=account
    ))


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    'assets',
    nargs=-1,
)
@click.option(
    "--pricethreshold",
    help="Percentage threshold for price",
    default=5.0,
    type=float)
@click.option(
    "--maxage",
    help="Max Age in minutes",
    default=60.0 * 24,
    type=float)
def feeds(ctx, assets, pricethreshold, maxage):
    """ Price Feed Overview
    """
    import builtins
    witnesses = Witnesses(bitshares_instance=ctx.bitshares)

    def test_price(p, ref):
        if (math.fabs((p / ref) - 1.0) > pricethreshold / 100.0):
            return click.style(str(p), fg="red")
        elif (math.fabs((p / ref) - 1.0) > pricethreshold / 2.0 / 100.0):
            return click.style(str(p), fg="yellow")
        else:
            return click.style(str(p), fg="green")

    def test_date(d):
        now = datetime.utcnow()
        if now < d + timedelta(minutes=maxage):
            return click.style(str(d), fg="green")
        if now < d + timedelta(minutes=maxage / 2.0):
            return click.style(str(d), fg="yellow")
        else:
            return click.style(str(d), fg="red")

    output = ""
    for asset in tqdm(assets):
        t = PrettyTable([
            "Asset",
            "Witness",
            "Date",
            "Settlement Price",
            "Core Exchange Price",
            "MCR",
            "SSPR"
        ])
        t.align = 'l'
        asset = Asset(asset, full=True, bitshares_instance=ctx.bitshares)
        current_feed = asset.feed
        feeds = asset.feeds
        producingwitnesses = builtins.set()
        for feed in tqdm(feeds):
            # if feed["witness"]["id"] not in witnesses.schedule:
            #     continue
            producingwitnesses.add(feed["witness"]["id"])
            t.add_row([
                asset["symbol"],
                feed["witness"].account["name"],
                test_date(feed["date"]),
                test_price(feed["settlement_price"], current_feed["settlement_price"]),
                test_price(feed["core_exchange_rate"], current_feed["core_exchange_rate"]),
                feed["maintenance_collateral_ratio"] / 10,
                feed["maximum_short_squeeze_ratio"] / 10,
            ])
        for missing in (builtins.set(witnesses.schedule).difference(producingwitnesses)):
            witness = Witness(missing)
            t.add_row([
                click.style(asset["symbol"], bg="red"),
                click.style(witness.account["name"], bg="red"),
                click.style(str(datetime(1970, 1, 1))),
                click.style("missing", bg="red"),
                click.style("missing", bg="red"),
                click.style("missing", bg="red"),
                click.style("missing", bg="red"),
            ])
        output += t.get_string(sortby="Date", reversesort=True)
        output += "\n"
    click.echo(output)


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    'symbol',
    type=str,
    nargs=1)
@click.argument(
    'price',
    type=float,
    nargs=1)
@click.argument(
    'market',
    type=str,
    nargs=1)
@click.option(
    "--account",
    help="Account that takes this action",
    default=config["default_account"],
    type=str)
@unlockWallet
def newfeed(ctx, symbol, price, market, account):
    """ Publish a price feed!

        Examples:

            \b
            uptick newfeed USD 0.01 USD/BTS
            uptick newfeed USD 100 BTS/USD
    """
    pprint(ctx.bitshares.publish_price_feed(
        symbol,
        Price(price, market)
    ))


if __name__ == '__main__':
    main()
