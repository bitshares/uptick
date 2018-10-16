import json
import click
import logging
import prettytable
import pkg_resources
from termcolor import colored
from bitshares.account import Account
from bitshares.amount import Amount
log = logging.getLogger(__name__)


def highlight(msg):
    return colored(msg, "yellow", attrs=['bold'])


def detail(msg):
    return colored(msg, "cyan", attrs=[])


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    for app in ["uptick", "bitshares", "graphenelib"]:
        print_message('{prog:<32} {version}'.format(
            prog=highlight(pkg_resources.require(app)[0].project_name),
            version=detail(pkg_resources.require(app)[0].version)
        ))
    ctx.exit()


def print_permissions(account):
    t = [["Permission", "Threshold", "Key/Account"]]
    for permission in ["owner", "active"]:
        auths = []
        # account auths:
        for authority in sorted(
            account[permission]["account_auths"],
            key=lambda x: x[1],
            reverse=True
        ):
            auths.append("%s (%d)" % (
                Account(authority[0])["name"], authority[1]))
        # key auths:
        for authority in sorted(
            account[permission]["key_auths"],
            key=lambda x: x[1],
            reverse=True
        ):
            auths.append("%s (%d)" % (authority[0], authority[1]))
        t.append([
            permission,
            account[permission]["weight_threshold"],
            "\n".join(auths),
        ])
    t.append([
        "memo", "n/a",
        account["options"]["memo_key"],
    ])
    print_table(t, hrules=True)


def get_terminal(text="Password", confirm=False, allowedempty=False):
    import getpass
    while True:
        pw = getpass.getpass(text)
        if not pw and not allowedempty:
            print_message("Cannot be empty!", "error")
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
                print_message("Not matching!", "warning")
    return pw


def print_tx(tx):
    click.echo(tx)


def print_table(table, hrules=False, align='l'):
    if not hrules:
        hrules = prettytable.FRAME
    else:
        hrules = prettytable.ALL

    t = prettytable.PrettyTable(
        table[0],
        hrules=hrules)
    t.align = align
    for row in table[1:]:
        t.add_row(row)
    click.echo(t)


def print_message(msg, mode="success"):
    click.echo(msg)


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
        return (
            "Transfer from {from_account[name]} to {to_account[name]}: {amount}"
            .format(**locals()))
    else:
        return json.dumps(op, indent=4)
