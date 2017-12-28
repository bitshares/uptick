import re
import json
import click
from pprint import pprint
from prettytable import PrettyTable
from bitshares.amount import Amount
from bitshares.blockchain import Blockchain
from bitshares.block import Block
from bitshares.account import Account
from bitshares.asset import Asset
from bitshares.storage import configStorage as config
from .decorators import (
    onlineChain,
    unlockWallet
)
from .main import main


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
            block = Block(obj, lazy=False, bitshares_instance=ctx.bitshares)
            t = PrettyTable(["Key", "Value"])
            t.align = "l"
            for key in sorted(block):
                value = block[key]
                if key == "transactions":
                    value = json.dumps(value, indent=4)
                t.add_row([key, value])
            click.echo(t)
        # Object Id
        elif re.match("^\d*\.\d*\.\d*$", obj):
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
        elif obj.upper() == obj and re.match("^[A-Z\.]*$", obj):
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
                click.echo("Public Key not known: %s" % obj)

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

        elif ":" in obj:
            vote = ctx.bitshares.rpc.lookup_vote_ids([obj])[0]
            if vote:
                t = PrettyTable(["Key", "Value"])
                t.align = "l"
                for key in sorted(vote):
                    value = vote[key]
                    if isinstance(value, dict) or isinstance(value, list):
                        value = json.dumps(value, indent=4)
                    t.add_row([key, value])
                click.echo(t)
            else:
                click.echo("voteid %s unknown" % obj)

        else:
            click.echo("Couldn't identify object to read")


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    'currency',
    type=str,
    required=False,
    default="USD"
)
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

    t = PrettyTable(["Operation", "Type", "Fee", currency])
    t.align = "l"
    t.align["Fee"] = "r"
    t.align[currency] = "r"

    for fee in fees:
        for f in fee[1]:
            t.add_row([
                getOperationNameForId(fee[0]),
                f,
                str(Amount({
                    "amount": fee[1].get(f, 0),
                    "asset_id": "1.3.0"
                })),
                str(price * Amount({
                    "amount": fee[1].get(f, 0),
                    "asset_id": "1.3.0"
                }))
            ])
    click.echo(t)
