import os
import hashlib
import yaml
import sys
import json
import click
from pprint import pprint
from prettytable import PrettyTable
from bitshares.account import Account
from bitshares.storage import configStorage as config
from .decorators import (
    onlineChain,
    unlockWallet,
    configfile
)
from .ui import (
    print_permissions,
    pprintOperation,
)
from .main import main


@main.group()
@onlineChain
@click.pass_context
@click.option(
    '--configfile',
    default="config.yaml",
    help="YAML file with configuration"
)
def api(ctx, configfile):
    """ Open an local API for trading bots
    """
    ctx.obj["configfile"] = configfile


@api.command()
@click.pass_context
def create(ctx):
    """ Create default config file
    """
    import shutil
    this_dir, this_filename = os.path.split(__file__)
    default_config_file = os.path.join(this_dir, "apis/example-config.yaml")
    config_file = ctx.obj["configfile"]
    shutil.copyfile(
        default_config_file,
        config_file
    )
    click.echo("Config file created: %s" % config_file)


@api.command()
@click.pass_context
@configfile
def start(ctx):
    """ Start the API according to the config file
    """
    module = ctx.config.get("api", "poloniex")
    # unlockWallet
    if module == "poloniex":
        from .apis import poloniex
        poloniex.run(ctx, port=5000)
    else:
        click.echo("Unkown 'api'!")


@api.command()
@click.option(
    '--password',
    prompt="Plain Text Password",
    hide_input=True,
    confirmation_prompt=False,
    help="Plain Text Password"
)
def apipassword(password):
    """ Generate a SHA256 hash of the password for the YAML
        configuration
    """
    click.echo(
        hashlib.sha256(bytes(password, "utf-8")).hexdigest()
    )
