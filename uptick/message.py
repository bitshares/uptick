import click
from bitshares.storage import configStorage as config
from bitshares.message import Message
from .decorators import (
    onlineChain,
    unlockWallet,
)
from .main import main


@main.group()
@click.pass_context
def message(ctx):
    pass


@message.command()
@click.pass_context
@onlineChain
@unlockWallet
@click.option(
    "--account",
    default=config["default_account"],
    type=str,
    help="Account to use"
)
@click.option(
    "--file",
    type=click.File('r')
)
def sign(ctx, file, account):
    """ Sign a message with an account
    """
    if not file:
        click.echo("Prompting for message. Terminate with CTRL-D")
        file = click.get_text_stream('stdin')
    m = Message(file.read(), bitshares_instance=ctx.bitshares)
    click.echo(m.sign(account))


@message.command()
@click.pass_context
@onlineChain
@click.option(
    "--account",
    default=config["default_account"],
    type=str,
    help="Account to use"
)
@click.option(
    "--file",
    type=click.File('r')
)
def verify(ctx, file, account):
    """ Verify a signed message
    """
    if not file:
        click.echo("Prompting for message. Terminate with CTRL-D")
        file = click.get_text_stream('stdin')
    m = Message(file.read(), bitshares_instance=ctx.bitshares)
    click.echo("Verified" if m.verify() else "not verified")
