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


@tools.command()
@click.pass_context
@online
@click.option("--limit", default=10, type=int)
def getbrainkeys(ctx, limit):
    """ Return keys for cloudlogin
    """
    from bitsharesbase.account import BrainKey

    password = click.prompt("Passphrase", hide_input=True).strip()
    t = [["index", "wif", "pubkey", "accounts"]]
    wif = BrainKey(password)
    for i in range(limit):
        pubkey = format(wif.get_public_key(), ctx.bitshares.rpc.chain_params["prefix"])

        t.append(
            [
                i,
                str(wif.get_private_key()),
                pubkey,
                ctx.bitshares.wallet.getAccountFromPublicKey(pubkey) or "",
            ]
        )
        next(wif)

    print_table(t)


@tools.command()
@click.argument("identifiers", nargs=-1)
def operation(identifiers):
    """ Get an operation name/id pair.

    IDENTIFIERS can be numbers, ranges (e.g. "5..9"), or partial
    operation names (e.g. "htlc").  If called with no arguments, lists
    all known operations.

    """
    from bitsharesbase.operations import operations, getOperationNameForId

    ret = [["id", "name"]]
    num_ops = len(operations)
    if identifiers==():
        identifiers = [i for i in range(num_ops)]
    for identifier in identifiers:
        try:
            id = int(identifier)
            name = getOperationNameForId(id)
            ret.append([id, name])
        except Exception:
            if ".." in identifier:
                bounds = identifier.split("..",1)
                for id in range(int(bounds[0]),min(int(bounds[1])+1,num_ops)):
                    name = getOperationNameForId(id)
                    ret.append([id, name])
            else:
                for key in [k for k in operations.keys() if identifier in k]:
                    id = operations[key]
                    name = getOperationNameForId(id)
                    ret.append([id, name])
    print_table(ret)
