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
