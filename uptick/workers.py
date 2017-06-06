import click
from bitshares.storage import configStorage as config
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
