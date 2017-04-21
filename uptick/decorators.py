import os
import json
import sys
from bitshares import BitShares
from bitshares.account import Account
from bitshares.amount import Amount
from bitshares.instance import set_shared_bitshares_instance
from prettytable import PrettyTable, ALL as allBorders
from functools import update_wrapper
import pkg_resources
import click
import logging
log = logging.getLogger(__name__)


def verbose(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        global log
        verbosity = [
            "critical", "error", "warn", "info", "debug"
        ][int(min(ctx.obj.get("verbose", 0), 4))]
        log.setLevel(getattr(logging, verbosity.upper()))
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setLevel(getattr(logging, verbosity.upper()))
        ch.setFormatter(formatter)
        log.addHandler(ch)

        # GrapheneAPI logging
        if ctx.obj["verbose"] > 4:
            verbosity = [
                "critical", "error", "warn", "info", "debug"
            ][int(min(ctx.obj.get("verbose", 4) - 4, 4))]
            log = logging.getLogger("grapheneapi")
            log.setLevel(getattr(logging, verbosity.upper()))
            log.addHandler(ch)

        if ctx.obj["verbose"] > 8:
            verbosity = [
                "critical", "error", "warn", "info", "debug"
            ][int(min(ctx.obj.get("verbose", 8) - 8, 4))]
            log = logging.getLogger("graphenebase")
            log.setLevel(getattr(logging, verbosity.upper()))
            log.addHandler(ch)

        return ctx.invoke(f, *args, **kwargs)
    return update_wrapper(new_func, f)


def offlineChain(f):
    @click.pass_context
    @verbose
    def new_func(ctx, *args, **kwargs):
        ctx.obj["offline"] = True
        ctx.bitshares = BitShares(**ctx.obj)
        set_shared_bitshares_instance(ctx.bitshares)
        return ctx.invoke(f, *args, **kwargs)
    return update_wrapper(new_func, f)


def onlineChain(f):
    @click.pass_context
    @verbose
    def new_func(ctx, *args, **kwargs):
        ctx.bitshares = BitShares(**ctx.obj)
        set_shared_bitshares_instance(ctx.bitshares)
        return ctx.invoke(f, *args, **kwargs)
    return update_wrapper(new_func, f)


def unlockWallet(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        if not ctx.obj.get("unsigned", False):
            if ctx.bitshares.wallet.created():
                if "UNLOCK" in os.environ:
                    pwd = os.environ["UNLOCK"]
                else:
                    pwd = click.prompt("Current Wallet Passphrase", hide_input=True)
                ctx.bitshares.wallet.unlock(pwd)
            else:
                click.echo("No wallet installed yet. Creating ...")
                pwd = click.prompt("Wallet Encryption Passphrase", hide_input=True, confirmation_prompt=True)
                ctx.bitshares.wallet.create(pwd)
        return ctx.invoke(f, *args, **kwargs)
    return update_wrapper(new_func, f)


# Aliases
chain = onlineChain
online = onlineChain
offline = offlineChain
unlock = unlockWallet
