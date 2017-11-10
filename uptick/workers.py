import json
import click
import datetime
from prettytable import PrettyTable
from bitshares.storage import configStorage as config
from bitshares.worker import Workers
from bitshares.account import Account
from bitshares.amount import Amount
from pprint import pprint
from .decorators import (
    onlineChain,
    unlockWallet
)
from .main import main


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    'workers',
    nargs=-1)
@click.option(
    "--account",
    default=config["default_account"],
    help="Account that takes this action",
    type=str)
@unlockWallet
def approveworker(ctx, workers, account):
    """ Approve worker(es)
    """
    pprint(ctx.bitshares.approveworker(
        workers,
        account=account
    ))


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    'workers',
    nargs=-1)
@click.option(
    "--account",
    help="Account that takes this action",
    default=config["default_account"],
    type=str)
@unlockWallet
def disapproveworker(ctx, workers, account):
    """ Disapprove worker(es)
    """
    pprint(ctx.bitshares.disapproveworker(
        workers,
        account=account
    ))


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    'account',
    default=None,
    required=False
)
def workers(ctx, account):
    """ List all workers (of an account)
    """
    workers = Workers(account)
    t = PrettyTable([
        "id",
        "name/url",
        "daily_pay",
        "votes",
        "time",
        "account",
    ])
    t.align["name/url"] = "l"
    t.align["account"] = "l"
    for worker in workers:
        if worker["work_end_date"] < datetime.datetime.utcnow():
            continue
        votes = Amount({
            "amount": worker["total_votes_for"],
            "asset_id": "1.3.0"})
        amount = Amount({
            "amount": worker["daily_pay"],
            "asset_id": "1.3.0"})
        t.add_row([
            worker["id"],
            "{name}\n{url}".format(**worker),
            str(amount),
            str(votes),
            "{work_begin_date:%Y-%m-%d}\n-\n{work_end_date:%Y-%m-%d}".format(**worker),
            str(Account(worker["worker_account"])["name"]),
        ])
    click.echo(t)
