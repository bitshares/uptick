import click
from .decorators import onlineChain, unlockWallet
from .ui import print_tx
from .main import main, config


@main.command()
@click.pass_context
@onlineChain
@click.argument("members", nargs=-1)
@click.option(
    "--account",
    default=config["default_account"],
    help="Account that takes this action",
    type=str,
)
@unlockWallet
def approvecommittee(ctx, members, account):
    """ Approve committee member(s)
    """
    print_tx(ctx.bitshares.approvecommittee(members, account=account))


@main.command()
@click.pass_context
@onlineChain
@click.argument("members", nargs=-1)
@click.option(
    "--account",
    help="Account that takes this action",
    default=config["default_account"],
    type=str,
)
@unlockWallet
def disapprovecommittee(ctx, members, account):
    """ Disapprove committee member(s)
    """
    print_tx(ctx.bitshares.disapprovecommittee(members, account=account))


@main.command()
@click.pass_context
@onlineChain
@click.argument("url", type=str)
@click.option(
    "--account",
    help="Account that takes this action",
    default=config["default_account"],
    type=str,
)
@unlockWallet
def createcommittee(ctx, url, account):
    """ Setup a committee account for your account
    """
    print_tx(ctx.bitshares.create_committee_member(url, account=account))
