import math
import click
from prettytable import PrettyTable
from pprint import pprint
from tqdm import tqdm
from bitshares.storage import configStorage as config
from bitshares.price import Price
from bitshares.witness import Witness, Witnesses
from bitshares.asset import Asset
from datetime import datetime, timedelta
from .decorators import (
    onlineChain,
    unlockWallet
)
from .main import main


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
            "Producer",
            "Active Witness",
            "Date",
            "Settlement Price",
            "Core Exchange Price",
            "MCR",
            "SSPR"
        ])
        t.align = 'c'
        t.align["Producer"] = 'l'
        asset = Asset(asset, full=True, bitshares_instance=ctx.bitshares)
        current_feed = asset.feed
        feeds = asset.feeds
        producingwitnesses = builtins.set()
        for feed in tqdm(feeds):
            producingwitnesses.add(feed["producer"]["id"])
            t.add_row([
                asset["symbol"],
                feed["producer"]["name"],
                click.style(
                    "X" if feed["producer"]["id"] in witnesses.schedule else "",
                    bold=True),
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
                click.style(
                    "x" if feed["producer"]["id"] in witnesses.schedule else "",
                    bold=True),
                click.style(str(datetime(1970, 1, 1))),
                click.style("missing", bg="red"),
                click.style("missing", bg="red"),
                click.style("missing", bg="red"),
                click.style("missing", bg="red"),
            ])
        output += t.get_string(sortby="Date", reversesort=True)
        output += "\n"
    click.echo(output)
