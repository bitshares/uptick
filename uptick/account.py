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
)
from .ui import (
    print_permissions,
    pprintOperation,
)
from .main import main


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    "foreign_account",
    required=False,
    type=str)
@click.option(
    "--account",
    default=config["default_account"],
    type=str,
    help="Account to be modified"
)
@click.option(
    "--permission",
    default="active",
    type=str,
    help="Permission/Role to be modified"
)
@click.option(
    "--threshold",
    type=int,
    help="Threshold for the Role"
)
@click.option(
    "--weight",
    type=int,
    help="Weight of the new key/account"
)
@unlockWallet
def allow(ctx, foreign_account, permission, weight, threshold, account):
    """ Add a key/account to an account's permission
    """
    if not foreign_account:
        from bitsharesbase.account import PasswordKey
        pwd = click.prompt(
            "Password for Key Derivation",
            hide_input=True,
            confirmation_prompt=True
        )
        foreign_account = format(
            PasswordKey(account, pwd, permission).get_public(),
            "BTS"
        )
    pprint(ctx.bitshares.allow(
        foreign_account,
        weight=weight,
        account=account,
        permission=permission,
        threshold=threshold
    ))


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    "foreign_account",
    type=str)
@click.option(
    "--account",
    default=config["default_account"],
    help="Account to be modified",
    type=str)
@click.option(
    "--permission",
    default="active",
    help="Permission/Role to be modified",
    type=str)
@click.option(
    "--threshold",
    help="Threshold for the Role",
    type=int)
@unlockWallet
def disallow(ctx, foreign_account, permission, threshold, account):
    """ Remove a key/account from an account's permission
    """
    pprint(ctx.bitshares.disallow(
        foreign_account,
        account=account,
        permission=permission,
        threshold=threshold
    ))


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    "account",
    nargs=-1)
@click.option(
    "--csv/--table",
    help="Show output as csv or table",
    default=False)
@click.option(
    "--type",
    type=str,
    help="Only show operations of this type",
    multiple=True)
@click.option(
    "--exclude",
    type=str,
    help="Exclude certain types",
    multiple=True)
@click.option(
    "--limit",
    type=int,
    help="Limit number of elements",
    default=15)
@click.option('--raw/--no-raw', default=False)
def history(ctx, account, limit, type, csv, exclude, raw):
    """ Show history of an account
    """
    from bitsharesbase.operations import getOperationNameForId
    header = ["#", "time (block)", "operation", "details"]
    if csv:
        import csv
        t = csv.writer(sys.stdout, delimiter=";")
        t.writerow(header)
    else:
        t = PrettyTable(header)
        t.align = "r"
        t.align["details"] = "l"

    for a in account:
        account = Account(a, bitshares_instance=ctx.bitshares)
        for b in account.history(
            limit=limit,
            only_ops=type,
            exclude_ops=exclude
        ):
            row = [
                b["id"].split(".")[2],
                "%s" % (b["block_num"]),
                "{} ({})".format(getOperationNameForId(b["op"][0]), b["op"][0]),
                pprintOperation(b) if not raw else json.dumps(b, indent=4),
            ]
            if csv:
                t.writerow(row)
            else:
                t.add_row(row)
    if not csv:
        click.echo(t)


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    "to",
    nargs=1,
    type=str)
@click.argument(
    "amount",
    nargs=1,
    type=float)
@click.argument(
    "asset",
    nargs=1,
    type=str)
@click.argument(
    "memo",
    required=False,
    type=str,
    default=None)
@click.option(
    "--account",
    default=config["default_account"],
    help="Account to send from"
)
@unlockWallet
def transfer(ctx, to, amount, asset, memo, account):
    """ Transfer assets
    """
    pprint(ctx.bitshares.transfer(
        to,
        amount,
        asset,
        memo=memo,
        account=account
    ))


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    "accounts",
    nargs=-1)
def balance(ctx, accounts):
    """ Show Account balances
    """
    t = PrettyTable(["Account", "Amount"])
    t.align = "r"
    for a in accounts:
        account = Account(a, bitshares_instance=ctx.bitshares)
        for b in account.balances:
            t.add_row([
                str(a),
                str(b),
            ])
    click.echo(str(t))


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    "account",
    nargs=1)
def permissions(ctx, account):
    """ Show permissions of an account
    """
    print_permissions(Account(account))


@main.command()
@click.pass_context
@onlineChain
@click.argument(
    "accountname",
    nargs=1,
    type=str)
@click.option(
    "--account",
    default=config["default_account"],
    help="Account to pay the registration fee"
)
@click.option(
    '--password',
    prompt="Account Password",
    hide_input=True,
    confirmation_prompt=True,
    help="Account Password"
)
@unlockWallet
def newaccount(ctx, accountname, account, password):
    """ Create a new account
    """
    pprint(ctx.bitshares.create_account(
        accountname,
        registrar=account,
        password=password,
    ))


@main.command(
    help="Upgrade Account"
)
@click.pass_context
@onlineChain
@click.argument(
    "account",
    nargs=1,
    default=config["default_account"],
    type=str)
@unlockWallet
def upgrade(ctx, account):
    pprint(ctx.bitshares.upgrade_account(account))
