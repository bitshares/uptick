import click
from prettytable import PrettyTable
from bitshares.witness import Witnesses
from .decorators import onlineChain, unlockWallet
from .main import main, config
from .ui import print_tx, print_table


@main.command()
@click.pass_context
@onlineChain
@click.argument("witnesses", nargs=-1)
@click.option(
    "--account",
    default=config["default_account"],
    help="Account that takes this action",
    type=str,
)
@unlockWallet
def approvewitness(ctx, witnesses, account):
    """ Approve witness(es)
    """
    print_tx(ctx.bitshares.approvewitness(witnesses, account=account))


@main.command()
@click.pass_context
@onlineChain
@click.argument("witnesses", nargs=-1)
@click.option(
    "--account",
    help="Account that takes this action",
    default=config["default_account"],
    type=str,
)
@unlockWallet
def disapprovewitness(ctx, witnesses, account):
    """ Disapprove witness(es)
    """
    print_tx(ctx.bitshares.disapprovewitness(witnesses, account=account))


@main.command()
@click.pass_context
@onlineChain
def witnesses(ctx):
    """ List witnesses and relevant information
    """
    t = [
        [
            "weight",
            "account",
            "signing_key",
            "vote_id",
            "url",
            "total_missed",
            "last_confirmed_block_num",
        ]
    ]
    for witness in sorted(Witnesses(), key=lambda x: x.weight, reverse=True):
        witness.refresh()
        t.append(
            [
                "{:.2f}%".format(witness.weight * 100),
                witness.account["name"],
                witness["signing_key"],
                witness["vote_id"],
                witness["url"],
                witness["total_missed"],
                witness["last_confirmed_block_num"],
            ]
        )
    print_table(t)
