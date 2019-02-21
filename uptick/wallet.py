import click
from tqdm import tqdm
from bitshares.account import Account
from .decorators import onlineChain, offlineChain, unlockWallet
from .main import main, config
from .ui import print_table, print_message


@main.command()
@click.pass_context
@click.option(
    "--password",
    prompt="Wallet Passphrase",
    hide_input=True,
    confirmation_prompt=True,
    help="New Wallet Passphrase",
)
@offlineChain
def createwallet(ctx, password):
    """ Change the wallet passphrase
    """
    ctx.bitshares.wallet.create(password)


@main.command()
@click.pass_context
@offlineChain
@click.option(
    "--new-password",
    prompt="New Wallet Passphrase",
    hide_input=True,
    confirmation_prompt=True,
    help="New Wallet Passphrase",
)
@unlockWallet
def changewalletpassphrase(ctx, new_password):
    """ Change the wallet passphrase
    """
    ctx.bitshares.wallet.changePassphrase(new_password)


@main.command()
@click.pass_context
@onlineChain
@click.argument("key", nargs=-1)
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
                default="exit",
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
        if name:  # only if a name to the key was found
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
@click.argument("pubkeys", nargs=-1)
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
@click.argument("pubkey", nargs=1)
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
    t = [["Available Key"]]
    for key in ctx.bitshares.wallet.getPublicKeys():
        t.append([key])
    print_table(t)


@main.command()
@click.pass_context
@onlineChain
def listaccounts(ctx):
    """ List accounts (for the connected network)
    """
    t = [["Name", "Key", "Owner", "Active", "Memo"]]
    for key in tqdm(ctx.bitshares.wallet.getPublicKeys(True)):
        for account in ctx.bitshares.wallet.getAccountsFromPublicKey(key):
            account = Account(account)
            is_owner = key in [x[0] for x in account["owner"]["key_auths"]]
            is_active = key in [x[0] for x in account["active"]["key_auths"]]
            is_memo = key == account["options"]["memo_key"]
            t.append([
                account["name"],
                key,
                "x" if is_owner else "",
                "x" if is_active else "",
                "x" if is_memo else "",
            ])
    print_table(t)


@main.command()
@click.pass_context
@onlineChain
@click.argument("account", nargs=1)
@click.option(
    "--role", type=click.Choice(["owner", "active", "memo"]), default="active"
)
@unlockWallet
def importaccount(ctx, account, role):
    """ Import an account using an account password
    """
    from bitsharesbase.account import PasswordKey

    password = click.prompt("Account Passphrase", hide_input=True)
    account = Account(account, bitshares_instance=ctx.bitshares)
    imported = False

    if role == "owner":
        owner_key = PasswordKey(account["name"], password, role="owner")
        owner_pubkey = format(
            owner_key.get_public_key(), ctx.bitshares.rpc.chain_params["prefix"]
        )
        if owner_pubkey in [x[0] for x in account["owner"]["key_auths"]]:
            print_message("Importing owner key!")
            owner_privkey = owner_key.get_private_key()
            ctx.bitshares.wallet.addPrivateKey(owner_privkey)
            imported = True

    if role == "active":
        active_key = PasswordKey(account["name"], password, role="active")
        active_pubkey = format(
            active_key.get_public_key(), ctx.bitshares.rpc.chain_params["prefix"]
        )
        if active_pubkey in [x[0] for x in account["active"]["key_auths"]]:
            print_message("Importing active key!")
            active_privkey = active_key.get_private_key()
            ctx.bitshares.wallet.addPrivateKey(active_privkey)
            imported = True

    if role == "memo":
        memo_key = PasswordKey(account["name"], password, role=role)
        memo_pubkey = format(
            memo_key.get_public_key(), ctx.bitshares.rpc.chain_params["prefix"]
        )
        if memo_pubkey == account["memo_key"]:
            print_message("Importing memo key!")
            memo_privkey = memo_key.get_private_key()
            ctx.bitshares.wallet.addPrivateKey(memo_privkey)
            imported = True

    if not imported:
        print_message("No matching key(s) found. Password correct?", "error")


@main.command()
@click.pass_context
@click.option(
    "--ignore-warning/--no-ignore-warning",
    prompt="Are you sure you want to wipe your wallet? This action is irreversible!",
)
@offlineChain
def wipewallet(ctx, ignore_warning):
    """ Wipe the wallet (keep configuration)
    """
    ctx.bitshares.wallet.wipe(ignore_warning)
