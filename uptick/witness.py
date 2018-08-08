import click
from prettytable import PrettyTable
from bitshares.witness import Witnesses
from pprint import pprint
from .decorators import (
    onlineChain,
    unlockWallet
)
from .main import main, config


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


@main.command()
@click.pass_context
@onlineChain
def witnesses(ctx):
    t = PrettyTable([
        "weight",
        "account",
        "signing_key",
        "vote_id",
        "url",
        "total_missed",
        "last_confirmed_block_num"
    ])
    t.align = 'l'
    for witness in sorted(
        Witnesses(),
        key=lambda x: x.weight,
        reverse=True
    ):
        witness.refresh()
        t.add_row([
            "{:.2f}%".format(witness.weight * 100),
            witness.account["name"],
            witness["signing_key"],
            witness["vote_id"],
            witness["url"],
            witness["total_missed"],
            witness["last_confirmed_block_num"]
        ])
    click.echo(t)
