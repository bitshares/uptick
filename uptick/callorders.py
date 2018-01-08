import sys
import click
from pprint import pprint
from prettytable import PrettyTable
from click_datetime import Datetime
from datetime import datetime, timedelta
from bitshares.storage import configStorage as config
from bitshares.market import Market
from bitshares.amount import Amount
from bitshares.account import Account
from bitshares.price import Price, Order
from .decorators import (
    onlineChain,
    unlockWallet,
    online,
    unlock
)
from .main import main


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    "obj",
    required=False,
    default=config["default_account"],
    type=str,
)
def calls(ctx, obj):
    """ List call/short positions of an account or an asset
    """
    if obj.upper() == obj:
        # Asset
        from bitshares.asset import Asset
        asset = Asset(obj, full=True)
        calls = asset.get_call_orders(10)
        t = PrettyTable(["acount", "debt", "collateral", "call price", "ratio"])
        t.align = 'r'
        for call in calls:
            t.add_row([
                str(call["account"]["name"]),
                str(call["debt"]),
                str(call["collateral"]),
                str(call["call_price"]),
                "%.2f" % (call["ratio"])
            ])
        click.echo(str(t))
    else:
        # Account
        from bitshares.dex import Dex
        dex = Dex(bitshares_instance=ctx.bitshares)
        calls = dex.list_debt_positions(account=obj)
        t = PrettyTable(["debt", "collateral", "call price", "ratio"])
        t.align = 'r'
        for symbol in calls:
            t.add_row([
                str(calls[symbol]["debt"]),
                str(calls[symbol]["collateral"]),
                str(calls[symbol]["call_price"]),
                "%.2f" % (calls[symbol]["ratio"])
            ])
        click.echo(str(t))


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    "asset",
    type=str,
)
def settlements(ctx, asset):
    """ Show pending settlement orders of a bitasset
    """
    from bitshares.asset import Asset
    asset = Asset(asset, full=True)
    if not asset.is_bitasset:
        click.echo("{} is not a bitasset.".format(asset["symbol"]))
        sys.exit(1)
    calls = asset.get_settle_orders(10)
    t = PrettyTable(["acount", "amount", "date"])
    t.align = 'r'
    for call in calls:
        t.add_row([
            str(call["account"]["name"]),
            str(call["amount"]),
            str(call["date"]),
        ])
    click.echo(str(t))
