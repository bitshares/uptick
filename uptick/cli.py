#!/usr/bin/env python3

import sys
import json
import click
import logging
from pprint import pprint
from bitshares.storage import configStorage as config
from bitshares.transactionbuilder import TransactionBuilder
from prettytable import PrettyTable
from .ui import (
    print_permissions,
    get_terminal,
    pprintOperation,
    print_version,
)
from .decorators import (
    onlineChain,
    offlineChain,
    unlockWallet
)
from .main import main
from . import (
    account,
    committee,
    feed,
    info,
    markets,
    proposal,
    wallet,
    witness,
    workers,
    api,
    callorders,
    vesting,
    message,
    rpc
)
log = logging.getLogger(__name__)


@main.command()
@click.pass_context
@offlineChain
@click.argument(
    'key',
    type=str
)
@click.argument(
    'value',
    type=str
)
def set(ctx, key, value):
    """ Set configuration parameters
    """
    if (key == "default_account" and
            value[0] == "@"):
        value = value[1:]
    config[key] = value


@main.command()
def configuration():
    """ Show configuration variables
    """
    t = PrettyTable(["Key", "Value"])
    t.align = "l"
    for key in config:
        if key not in [
            "encrypted_master_password"
        ]:
            t.add_row([key, config[key]])
    click.echo(t)


@main.command()
@click.pass_context
@offlineChain
@click.argument(
    'filename',
    required=False,
    type=click.File('r'))
@unlockWallet
def sign(ctx, filename):
    """ Sign a json-formatted transaction
    """
    if filename:
        tx = filename.read()
    else:
        tx = sys.stdin.read()
    tx = TransactionBuilder(eval(tx), bitshares_instance=ctx.bitshares)
    tx.appendMissingSignatures()
    tx.sign()
    pprint(tx.json())


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    'filename',
    required=False,
    type=click.File('r'))
def broadcast(ctx, filename):
    """ Broadcast a json-formatted transaction
    """
    if filename:
        tx = filename.read()
    else:
        tx = sys.stdin.read()
    tx = TransactionBuilder(eval(tx), bitshares_instance=ctx.bitshares)
    tx.broadcast()
    pprint(tx.json())


@main.command()
@click.option(
    '--prefix',
    type=str,
    default="BTS",
    help="The refix to use"
)
@click.option(
    '--num',
    type=int,
    default=1,
    help="The number of keys to derive"
)
def randomwif(prefix, num):
    """ Obtain a random private/public key pair
    """
    from bitsharesbase.account import PrivateKey
    t = PrettyTable(["wif", "pubkey"])
    for n in range(0, num):
        wif = PrivateKey()
        t.add_row([
            str(wif),
            format(wif.pubkey, prefix)
        ])
    click.echo(str(t))


if __name__ == '__main__':
    main()
