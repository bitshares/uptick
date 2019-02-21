import re
import json
import click
from prettytable import PrettyTable
from bitshares.amount import Amount
from bitshares.blockchain import Blockchain
from bitshares.block import Block
from bitshares.account import Account
from bitshares.asset import Asset
from .decorators import onlineChain
from .main import main, config
from .ui import print_table, print_message, format_tx, highlight, detail


@main.command()
@click.pass_context
@onlineChain
@click.argument("objects", type=str, nargs=-1)
def info(ctx, objects):
    """ Obtain all kinds of information
    """
    if not objects:
        t = [["Key", "Value"]]
        info = ctx.bitshares.rpc.get_dynamic_global_properties()
        for key in info:
            t.append([key, info[key]])
        print_table(t)

    for obj in objects:
        # Block
        if re.match("^[0-9]*$", obj):
            block = Block(obj, lazy=False, bitshares_instance=ctx.bitshares)
            t = [["Key", "Value"]]
            for key in sorted(block):
                value = block[key]
                if key == "transactions":
                    value = format_tx(value)
                t.append([key, value])
            print_table(t)
        # Object Id
        elif re.match("^\d*\.\d*\.\d*$", obj):
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

        # Asset
        elif obj.upper() == obj and re.match("^[A-Z\.]*$", obj):
            data = Asset(obj)
            t = [["Key", "Value"]]
            for key in sorted(data):
                value = data[key]
                if isinstance(value, dict):
                    value = format_tx(value)
                t.append([key, value])
            print_table(t)

        # Public Key
        elif re.match("^BTS.{48,55}$", obj):
            account = ctx.bitshares.wallet.getAccountFromPublicKey(obj)
            if account:
                t = [["Account"]]
                t.append([account])
                print_table(t)
            else:
                print_message("Public Key not known: %s" % obj, "warning")

        # Account name
        elif re.match("^[a-zA-Z0-9\-\._]{2,64}$", obj):
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

        elif ":" in obj:
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

        else:
            print_message("Couldn't identify object to read", "warning")


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
            t.append(
                [
                    highlight(getOperationNameForId(fee[0])),
                    detail(f),
                    detail(
                        str(Amount({"amount": fee[1].get(f, 0), "asset_id": "1.3.0"}))
                    ),
                    detail(
                        str(
                            price
                            * Amount({"amount": fee[1].get(f, 0), "asset_id": "1.3.0"})
                        )
                    ),
                ]
            )
    print_table(t)
