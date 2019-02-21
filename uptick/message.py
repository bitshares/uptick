import click
from bitshares.message import Message, InvalidMessageSignature
from .decorators import onlineChain, unlockWallet
from .main import main, config
from .ui import print_message


@main.group()
@click.pass_context
def message(ctx):
    """ Sub-command to deal with signed messages
    """
    pass


@message.command()
@click.pass_context
@onlineChain
@unlockWallet
@click.option(
    "--account", default=config["default_account"], type=str, help="Account to use"
)
@click.option("--file", type=click.File("r"))
def sign(ctx, file, account):
    """ Sign a message with an account
    """
    if not file:
        print_message("Prompting for message. Terminate with CTRL-D", "info")
        file = click.get_text_stream("stdin")
    m = Message(file.read(), bitshares_instance=ctx.bitshares)
    print_message(m.sign(account), "info")


@message.command()
@click.pass_context
@onlineChain
@click.option(
    "--account", default=config["default_account"], type=str, help="Account to use"
)
@click.option("--file", type=click.File("r"))
def verify(ctx, file, account):
    """ Verify a signed message
    """
    if not file:
        print_message("Prompting for message. Terminate with CTRL-D", "info")
        file = click.get_text_stream("stdin")
    m = Message(file.read(), bitshares_instance=ctx.bitshares)
    try:
        if m.verify():
            print_message("Verified", "success")
        else:
            print_message("not verified", "error")
    except InvalidMessageSignature:
        print_message("Signature INVALID!", "error")
