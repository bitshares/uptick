import os
import hashlib
import yaml
import sys
import json
import click
from prettytable import PrettyTable
from bitshares.account import Account
from .decorators import onlineChain, unlockWallet, configfile
from .main import main, config
from .ui import print_message


@main.group()
@onlineChain
@click.pass_context
@click.option(
    "--configfile", default="config.yaml", help="YAML file with configuration"
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
    shutil.copyfile(default_config_file, config_file)
    print_message("Config file created: {}".format(config_file))


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
        print_message("Unkown 'api'!", "error")


@api.command()
@click.option(
    "--password",
    prompt="Plain Text Password",
    hide_input=True,
    confirmation_prompt=False,
    help="Plain Text Password",
)
def apipassword(password):
    """ Generate a SHA256 hash of the password for the YAML
        configuration
    """
    print_message(hashlib.sha256(bytes(password, "utf-8")).hexdigest(), "info")
