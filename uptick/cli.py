#!/usr/bin/env python3

import sys
import json
import click
import logging
from bitshares.transactionbuilder import TransactionBuilder
from prettytable import PrettyTable
from .ui import print_permissions, get_terminal, print_version
from .decorators import onlineChain, offlineChain, unlockWallet
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
    rpc,
    votes,
)
from .ui import print_message, print_table, print_tx

log = logging.getLogger(__name__)


@main.command()
@click.pass_context
@offlineChain
@click.argument("key", type=str)
@click.argument("value", type=str)
def set(ctx, key, value):
    """ Set configuration parameters
    """
    if key == "default_account" and value[0] == "@":
        value = value[1:]
    ctx.bitshares.config[key] = value


@main.command()
@click.pass_context
@offlineChain
def configuration(ctx):
    """ Show configuration variables
    """
    t = [["Key", "Value"]]
    for key in ctx.bitshares.config:
        t.append([key, ctx.bitshares.config[key]])
    print_table(t)


@main.command()
@click.pass_context
@offlineChain
@click.argument("filename", required=False, type=click.File("r"))
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
    print_tx(tx.json())


@main.command()
@click.pass_context
@onlineChain
@click.argument("filename", required=False, type=click.File("r"))
def broadcast(ctx, filename):
    """ Broadcast a json-formatted transaction
    """
    if filename:
        tx = filename.read()
    else:
        tx = sys.stdin.read()
    tx = TransactionBuilder(eval(tx), bitshares_instance=ctx.bitshares)
    tx.broadcast()
    print_tx(tx.json())


@main.command()
@click.option("--prefix", type=str, default="BTS", help="The refix to use")
@click.option("--num", type=int, default=1, help="The number of keys to derive")
def randomwif(prefix, num):
    """ Obtain a random private/public key pair
    """
    from bitsharesbase.account import PrivateKey

    t = [["wif", "pubkey"]]
    for n in range(0, num):
        wif = PrivateKey()
        t.append([str(wif), format(wif.pubkey, prefix)])
    print_table(t)


if __name__ == "__main__":
    main()
