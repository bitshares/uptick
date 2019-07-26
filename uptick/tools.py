# -*- coding: utf-8 -*-
import click
from .decorators import online
from .main import main, config
from .ui import print_table, print_tx


@main.group()
def tools():
    """ Further tools
    """
    pass


@tools.command()
@click.pass_context
@online
@click.argument("account")
def getcloudloginkey(ctx, account):
    """ Return keys for cloudlogin
    """
    from bitsharesbase.account import PasswordKey

    password = click.prompt("Passphrase", hide_input=True).strip()
    t = [["role", "wif", "pubkey", "accounts"]]
    for role in ["owner", "active", "memo"]:
        wif = PasswordKey(account, password, role=role)
        pubkey = format(wif.get_public_key(), ctx.bitshares.rpc.chain_params["prefix"])

        t.append(
            [
                role,
                str(wif.get_private_key()),
                pubkey,
                ctx.bitshares.wallet.getAccountFromPublicKey(pubkey) or "",
            ]
        )

    print_table(t)
