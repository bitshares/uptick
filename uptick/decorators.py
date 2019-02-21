import os
import yaml
import click
import logging
from bitshares import BitShares
from bitshares.exceptions import WrongMasterPasswordException
from bitshares.instance import set_shared_bitshares_instance
from functools import update_wrapper
from .ui import print_message

log = logging.getLogger(__name__)


def verbose(f):
    """ Add verbose flags and add logging handlers
    """

    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        global log
        verbosity = ["critical", "error", "warn", "info", "debug"][
            int(min(ctx.obj.get("verbose", 0), 4))
        ]
        log.setLevel(getattr(logging, verbosity.upper()))
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch = logging.StreamHandler()
        ch.setLevel(getattr(logging, verbosity.upper()))
        ch.setFormatter(formatter)
        log.addHandler(ch)

        # GrapheneAPI logging
        if ctx.obj.get("verbose", 0) > 4:
            verbosity = ["critical", "error", "warn", "info", "debug"][
                int(min(ctx.obj.get("verbose", 4) - 4, 4))
            ]
            log = logging.getLogger("grapheneapi")
            log.setLevel(getattr(logging, verbosity.upper()))
            log.addHandler(ch)

        if ctx.obj.get("verbose", 0) > 8:
            verbosity = ["critical", "error", "warn", "info", "debug"][
                int(min(ctx.obj.get("verbose", 8) - 8, 4))
            ]
            log = logging.getLogger("graphenebase")
            log.setLevel(getattr(logging, verbosity.upper()))
            log.addHandler(ch)

        return ctx.invoke(f, *args, **kwargs)

    return update_wrapper(new_func, f)


def offline(f):
    """ This decorator allows you to access ``ctx.bitshares`` which is
        an instance of BitShares with ``offline=True``.
    """

    @click.pass_context
    @verbose
    def new_func(ctx, *args, **kwargs):
        ctx.obj["offline"] = True
        ctx.bitshares = BitShares(**ctx.obj)
        ctx.blockchain = ctx.bitshares
        ctx.bitshares.set_shared_instance()
        return ctx.invoke(f, *args, **kwargs)

    return update_wrapper(new_func, f)


def customchain(**kwargsChain):
    """ This decorator allows you to access ``ctx.bitshares`` which is
        an instance of BitShares. But in contrast to @chain, this is a
        decorator that expects parameters that are directed right to
        ``BitShares()``.

        ... code-block::python

                @main.command()
                @click.option("--worker", default=None)
                @click.pass_context
                @customchain(foo="bar")
                @unlock
                def list(ctx, worker):
                   print(ctx.obj)

    """

    def wrap(f):
        @click.pass_context
        @verbose
        def new_func(ctx, *args, **kwargs):
            newoptions = ctx.obj
            newoptions.update(kwargsChain)
            ctx.bitshares = BitShares(**newoptions)
            ctx.blockchain = ctx.bitshares
            set_shared_bitshares_instance(ctx.bitshares)
            return ctx.invoke(f, *args, **kwargs)

        return update_wrapper(new_func, f)

    return wrap


def chain(f):
    """ This decorator allows you to access ``ctx.bitshares`` which is
        an instance of BitShares.
    """

    @click.pass_context
    @verbose
    def new_func(ctx, *args, **kwargs):
        ctx.bitshares = BitShares(**ctx.obj)
        ctx.blockchain = ctx.bitshares
        set_shared_bitshares_instance(ctx.bitshares)
        return ctx.invoke(f, *args, **kwargs)

    return update_wrapper(new_func, f)


def unlock(f):
    """ This decorator will unlock the wallet by either asking for a
        passphrase or taking the environmental variable ``UNLOCK``
    """

    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        if not ctx.obj.get("unsigned", False):
            if ctx.bitshares.wallet.created():
                while True:
                    if "UNLOCK" in os.environ:
                        pwd = os.environ["UNLOCK"]
                    else:
                        pwd = click.prompt("Current Wallet Passphrase", hide_input=True)
                    try:
                        ctx.bitshares.wallet.unlock(pwd)
                    except WrongMasterPasswordException:
                        print_message("Incorrect Wallet passphrase!", "error")
                        continue
                    break
            else:
                print_message("No wallet installed yet. Creating ...", "warning")
                if "UNLOCK" in os.environ:
                    pwd = os.environ["UNLOCK"]
                else:
                    pwd = click.prompt(
                        "Wallet Encryption Passphrase",
                        hide_input=True,
                        confirmation_prompt=True,
                    )
                ctx.bitshares.wallet.create(pwd)
        return ctx.invoke(f, *args, **kwargs)

    return update_wrapper(new_func, f)


def configfile(f):
    """ This decorator will parse a configuration file in YAML format
        and store the dictionary in ``ctx.config``
    """

    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        ctx.config = yaml.load(open(ctx.obj["configfile"]))
        return ctx.invoke(f, *args, **kwargs)

    return update_wrapper(new_func, f)


# Aliases
onlineChain = chain
online = chain
offlineChain = offline
unlockWallet = unlock
