# -*- coding: utf-8 -*-
import re
import click
from bitshares.amount import Amount
from bitshares.blockchain import Blockchain
from bitshares.block import Block
from bitshares.account import Account
from bitshares.asset import Asset
from .decorators import onlineChain
from .main import main
from .ui import print_table, print_message, format_tx, highlight, detail


def status(ctx):
    t = [["Key", "Value"]]
    info = ctx.bitshares.rpc.get_dynamic_global_properties()
    for key in info:
        t.append([key, info[key]])
    print_table(t)


def block(ctx, obj):
    block = Block(obj, lazy=False, bitshares_instance=ctx.bitshares)
    t = [["Key", "Value"]]
    for key in sorted(block):
        value = block[key]
        if key == "transactions":
            value = format_tx(value)
        t.append([key, value])
    print_table(t)


def objectid(ctx, obj):
    data = ctx.bitshares.rpc.get_object(obj)
    if data:
        t = [["Key", "Value"]]
        for key in sorted(data):
            value = data[key]
            if isinstance(value, dict) or isinstance(value, list):
                value = format_tx(value)
            t.append([key, value])
        print_table(t)
    else:
        print_message("Object %s unknown" % obj, "warning")


def asset(ctx, obj):
    data = Asset(obj, full=True)
    t = [["Key", "Value"]]
    for key in sorted(data):
        value = data[key]
        if isinstance(value, dict):
            value = format_tx(value)
        t.append([key, value])
    print_table(t)


def pubkey(ctx, obj):
    accounts_gen = ctx.bitshares.wallet.getAccountsFromPublicKey(obj)
    accounts = [i for i in accounts_gen]
    if accounts:
        t = [["Account ID", "Name"]]
        for acc_id in accounts:
            A = Account(acc_id)
            t.append([acc_id, A.name])
        print_table(t)
    else:
        print_message("Public Key not known: %s" % obj, "warning")


def account(ctx, obj):
    account = Account(obj, full=True)
    if account:
        t = [["Key", "Value"]]
        for key in sorted(account):
            value = account[key]
            if isinstance(value, dict) or isinstance(value, list):
                value = format_tx(value)
            t.append([key, value])
        print_table(t)
    else:
        print_message("Account %s unknown" % obj, "warning")


def vote(ctx, obj):
    vote = ctx.bitshares.rpc.lookup_vote_ids([obj])[0]
    if vote:
        t = [["Key", "Value"]]
        for key in sorted(vote):
            value = vote[key]
            if isinstance(value, dict) or isinstance(value, list):
                value = format_tx(value)
            t.append([key, value])
        print_table(t)
    else:
        print_message("voteid %s unknown" % obj, "warning")


def process_object(ctx, obj):
    if re.match("^[0-9]*$", obj):
        # Block
        block(ctx, obj)
    elif re.match(r"^\d*\.\d*\.\d*$", obj):
        # Object Id
        objectid(ctx, obj)
    elif obj.upper() == obj and re.match(r"^[A-Z][A-Z0-9\.]{2,15}$", obj):
        # Asset
        asset(ctx, obj)
    elif re.match("^"+ctx.blockchain.prefix+".{48,55}$", obj):
        # Public Key
        pubkey(ctx, obj)
    elif re.match(r"^[a-zA-Z0-9\-\._]{2,64}$", obj):
        # Account name
        account(ctx, obj)
    elif ":" in obj:
        # Vote id
        vote(ctx, obj)
    else:
        print_message("Couldn't identify object to read", "warning")


@main.command()
@click.pass_context
@onlineChain
@click.argument("objects", type=str, nargs=-1)
def info(ctx, objects):
    """ Obtain all kinds of information
    """
    if not objects:
        status(ctx)

    for obj in objects:
        process_object(ctx, obj)


@main.command()
@click.pass_context
@onlineChain
@click.argument("currency", type=str, required=False, default="USD")
def fees(ctx, currency):
    """ List fees
    """
    from bitsharesbase.operationids import getOperationNameForId
    from bitshares.market import Market

    market = Market("%s:%s" % (currency, "BTS"))
    ticker = market.ticker()
    if "quoteSettlement_price" in ticker:
        price = ticker.get("quoteSettlement_price")
    else:
        price = ticker.get("latest", 0)
    price.invert()

    chain = Blockchain(bitshares_instance=ctx.bitshares)
    feesObj = chain.chainParameters().get("current_fees")
    fees = feesObj["parameters"]

    t = [["Operation", "Type", "Fee", currency]]

    for fee in fees:
        for f in fee[1]:
            data = [
                highlight(getOperationNameForId(fee[0])),
                detail(f),
                detail(Amount({"amount": fee[1].get(f, 0), "asset_id": "1.3.0"})),
                detail(
                    price * Amount({"amount": fee[1].get(f, 0), "asset_id": "1.3.0"})
                ),
            ]
            t.append(data)
    print_table(t)
