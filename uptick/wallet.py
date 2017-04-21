import click
from bitshares.storage import configStorage as config
from bitshares.account import Account
from pprint import pprint
from prettytable import PrettyTable
from .decorators import (
    onlineChain,
    offlineChain,
    unlockWallet
)
from .main import main


@main.command()
@click.pass_context
@offlineChain
@click.option(
    '--new-password',
    prompt="New Wallet Passphrase",
    hide_input=True,
    confirmation_prompt=True,
    help="New Wallet Passphrase"
)
@unlockWallet
def changewalletpassphrase(ctx, new_password):
    """ Change the wallet passphrase
    """
    ctx.bitshares.wallet.changePassphrase(new_password)


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    "key",
    nargs=-1
)
@unlockWallet
def addkey(ctx, key):
    """ Add a private key to the wallet
    """
    if not key:
        while True:
            key = click.prompt(
                "Private Key (wif) [Enter to quit]",
                hide_input=True,
                show_default=False,
                default="exit"
            )
            if not key or key == "exit":
                break
            try:
                ctx.bitshares.wallet.addPrivateKey(key)
            except Exception as e:
                click.echo(str(e))
                continue
    else:
        for k in key:
            try:
                ctx.bitshares.wallet.addPrivateKey(k)
            except Exception as e:
                click.echo(str(e))

    installedKeys = ctx.bitshares.wallet.getPublicKeys()
    if len(installedKeys) == 1:
        name = ctx.bitshares.wallet.getAccountFromPublicKey(installedKeys[0])
        account = Account(name, bitshares_instance=ctx.bitshares)
        click.echo("=" * 30)
        click.echo("Setting new default user: %s" % account["name"])
        click.echo()
        click.echo("You can change these settings with:")
        click.echo("    uptick set default_account <account>")
        click.echo("=" * 30)
        config["default_account"] = account["name"]


@main.command()
@click.pass_context
@offlineChain
@click.argument(
    "pubkeys",
    nargs=-1
)
def delkey(ctx, pubkeys):
    """ Delete a private key from the wallet
    """
    if not pubkeys:
        pubkeys = click.prompt("Public Keys").split(" ")
    if click.confirm(
        "Are you sure you want to delete keys from your wallet?\n"
        "This step is IRREVERSIBLE! If you don't have a backup, "
        "You may lose access to your account!"
    ):
        for pub in pubkeys:
            ctx.bitshares.wallet.removePrivateKeyFromPublicKey(pub)


@main.command()
@click.pass_context
@offlineChain
@click.argument(
    "pubkey",
    nargs=1
)
@unlockWallet
def getkey(ctx, pubkey):
    """ Obtain private key in WIF format
    """
    click.echo(ctx.bitshares.wallet.getPrivateKeyForPublicKey(pubkey))


@main.command()
@click.pass_context
@offlineChain
def listkeys(ctx):
    """ List all keys (for all networks)
    """
    t = PrettyTable(["Available Key"])
    t.align = "l"
    for key in ctx.bitshares.wallet.getPublicKeys():
        t.add_row([key])
    click.echo(t)


@main.command()
@click.pass_context
@onlineChain
def listaccounts(ctx):
    """ List accounts (for the connected network)
    """
    t = PrettyTable(["Name", "Type", "Available Key"])
    t.align = "l"
    for account in ctx.bitshares.wallet.getAccounts():
        t.add_row([
            account["name"] or "n/a",
            account["type"] or "n/a",
            account["pubkey"]
        ])
    click.echo(t)
