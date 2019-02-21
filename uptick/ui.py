import json
import click
import logging
import prettytable
import pkg_resources
from bitshares.account import Account
from bitshares.amount import Amount

log = logging.getLogger(__name__)


def format_dict(tx):
    from pygments import highlight, lexers, formatters

    json_raw = json.dumps(tx, sort_keys=True, indent=4)
    return highlight(
        bytes(json_raw, "UTF-8"), lexers.JsonLexer(), formatters.TerminalFormatter()
    )


def format_tx(tx):
    return format_dict(tx)


def print_tx(tx):
    click.echo(format_tx(tx))


def print_dict(tx):
    click.echo(format_dict(tx))


def print_message(msg, mode="success"):
    if mode == "success":
        click.echo(click.style(str(msg), fg="green"))
    elif mode == "warning":
        click.echo(click.style(str(msg), fg="yellow"))
    elif mode == "error":
        click.echo(click.style(str(msg), fg="red"))
    elif mode == "info":
        click.echo(click.style(str(msg), fg="magenta"))
    else:
        raise ValueError


def highlight(msg):
    return click.style(msg, fg="yellow", bold=True)


def detail(msg):
    return click.style(msg, fg="cyan")


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    t = [["name", "version"]]
    for app in ["uptick", "bitshares", "graphenelib"]:
        t.append(
            [
                highlight(pkg_resources.require(app)[0].project_name),
                detail(pkg_resources.require(app)[0].version),
            ]
        )
    print_table(t)
    ctx.exit()


def print_permissions(account):
    t = [["Permission", "Threshold", "Key/Account"]]
    for permission in ["owner", "active"]:
        auths = []
        # account auths:
        for authority in sorted(
            account[permission]["account_auths"], key=lambda x: x[1], reverse=True
        ):
            auths.append("%s (%d)" % (Account(authority[0])["name"], authority[1]))
        # key auths:
        for authority in sorted(
            account[permission]["key_auths"], key=lambda x: x[1], reverse=True
        ):
            auths.append("%s (%d)" % (authority[0], authority[1]))
        t.append(
            [permission, account[permission]["weight_threshold"], "\n".join(auths)]
        )
    t.append(["memo", "n/a", account["options"]["memo_key"]])
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
            pwck = getpass.getpass("Confirm " + text)
            if pw == pwck:
                break
            else:
                print_message("Not matching!", "warning")
    return pw


def format_table(table, hrules=False, align="l"):
    if not hrules:
        hrules = prettytable.FRAME
    else:
        hrules = prettytable.ALL

    header = [click.style(x, fg="red", bold=True) for x in table[0]]
    t = prettytable.PrettyTable(header, hrules=hrules)
    t.align = align
    for index, row in enumerate(table[1:]):
        row = [str(x) for x in row]
        row[0] = click.style(row[0], fg="yellow")
        t.add_row(row)
    return t


def print_table(*args, **kwargs):
    """
    if csv:
        import csv
        t = csv.writer(sys.stdout, delimiter=";")
        t.writerow(header)
    else:
        t = PrettyTable(header)
        t.align = "r"
        t.align["details"] = "l"
    """
    t = format_table(*args, **kwargs)
    click.echo(t)


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
    elif id == 6:
        return "Account {} updated".format(Account(op["account"])["name"])
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
        return format_dict(op)
