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


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    for app in ["uptick", "bitshares", "graphenelib"]:
        click.echo('{prog} {version}'.format(
            prog=pkg_resources.require(app)[0].project_name,
            version=pkg_resources.require(app)[0].version
        ))
    ctx.exit()


def print_permissions(account):
    t = PrettyTable(["Permission", "Threshold", "Key/Account"], hrules=allBorders)
    t.align = "r"
    for permission in ["owner", "active"]:
        auths = []
        # account auths:
        for authority in account[permission]["account_auths"]:
            auths.append("%s (%d)" % (Account(authority[0])["name"], authority[1]))
        # key auths:
        for authority in account[permission]["key_auths"]:
            auths.append("%s (%d)" % (authority[0], authority[1]))
        t.add_row([
            permission,
            account[permission]["weight_threshold"],
            "\n".join(auths),
        ])
    click.echo(t)


def get_terminal(text="Password", confirm=False, allowedempty=False):
    import getpass
    while True:
        pw = getpass.getpass(text)
        if not pw and not allowedempty:
            click.echo("Cannot be empty!")
            continue
        else:
            if not confirm:
                break
            pwck = getpass.getpass(
                "Confirm " + text
            )
            if (pw == pwck):
                break
            else:
                click.echo("Not matching!")
    return pw


def pprintOperation(op):
    from bitshares.price import Order, FilledOrder
    id = op["op"][0]
    op = op["op"][1]
    if id == 1:
        return str(Order(op))
    elif id == 4:
        return str(FilledOrder(op))
    elif id == 5:
        return "New account created for {}".format(op["name"])
    elif id == 2:
        return "Canceled order %s" % op["order"]
    elif id == 33:
        return "Claiming from vesting: %s" % str(Amount(op["amount"]))
    elif id == 15:
        return "Reserve {}".format(str(Amount(op["amount_to_reserve"])))
    elif id == 0:
        from_account = Account(op["from"])
        to_account = Account(op["to"])
        amount = Amount(op["amount"])
        return "Transfer from {from_account[name]} to {to_account[name]}: {amount}".format(
            **locals()
        )
    else:
        return json.dumps(op, indent=4)
