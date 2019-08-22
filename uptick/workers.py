# -*- coding: utf-8 -*-
import json
import click
import datetime
from bitshares.worker import Workers
from bitshares.account import Account
from bitshares.amount import Amount
from .decorators import onlineChain, unlockWallet
from .main import main, config
from .ui import print_table, print_tx


@main.command()
@click.pass_context
@onlineChain
@click.argument("workers", nargs=-1)
@click.option(
    "--account",
    default=config["default_account"],
    help="Account that takes this action",
    type=str,
)
@unlockWallet
def approveworker(ctx, workers, account):
    """ Approve worker(es)
    """
    print_tx(ctx.bitshares.approveworker(workers, account=account))


@main.command()
@click.pass_context
@onlineChain
@click.argument("workers", nargs=-1)
@click.option(
    "--account",
    help="Account that takes this action",
    default=config["default_account"],
    type=str,
)
@unlockWallet
def disapproveworker(ctx, workers, account):
    """ Disapprove worker(es)
    """
    print_tx(ctx.bitshares.disapproveworker(workers, account=account))


@main.command()
@click.pass_context
@onlineChain
@click.argument("account", default=None, required=False)
@click.option("--top", type=int)
@click.option("--sort", default="total_votes_for")
def workers(ctx, account, top, sort):
    """ List all workers (of an account)
    """

    def normalize_sort_keys(name):
        if name == "votes":
            return "total_votes_for"
        return name

    workers = Workers(account)
    t = [["id", "name/url", "daily_pay", "votes", "time", "account"]]
    sort = sort
    sort = normalize_sort_keys(sort)
    if sort in ["total_votes_for"]:
        workers_sorted = sorted(workers, key=lambda x: int(x[sort]), reverse=True)
    elif sort == "id":
        workers_sorted = sorted(
            workers, key=lambda x: int(x[sort].split(".")[2]), reverse=True
        )
    else:
        workers_sorted = sorted(workers, key=lambda x: x[sort], reverse=True)
    if top:
        workers_sorted = workers_sorted[: top + 1]
    for worker in workers_sorted:
        if worker["work_end_date"] < datetime.datetime.utcnow():
            continue
        votes = Amount({"amount": worker["total_votes_for"], "asset_id": "1.3.0"})
        amount = Amount({"amount": worker["daily_pay"], "asset_id": "1.3.0"})
        t.append(
            [
                worker["id"],
                "{name}\n{url}".format(**worker),
                str(amount),
                str(votes),
                "{work_begin_date:%Y-%m-%d}\n-\n{work_end_date:%Y-%m-%d}".format(
                    **worker
                ),
                str(Account(worker["worker_account"])["name"]),
            ]
        )
    print_table(t)
