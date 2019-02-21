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
def workers(ctx, account):
    """ List all workers (of an account)
    """
    workers = Workers(account)
    t = [["id", "name/url", "daily_pay", "votes", "time", "account"]]
    for worker in workers:
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
