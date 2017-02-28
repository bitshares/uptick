import json
import sys
from bitshares.account import Account
from prettytable import PrettyTable, ALL as allBorders
import pkg_resources
import click


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo('{prog} {version}'.format(
        prog=pkg_resources.require("uptick")[0].project_name,
        version=pkg_resources.require("uptick")[0].version
    ))
    ctx.exit()


def confirm(question, default="yes"):
    """ Confirmation dialog that requires *manual* input.

        :param str question: Question to ask the user
        :param str default: default answer
        :return: Choice of the user
        :rtype: bool

    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)
    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


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
    print(t)


def get_terminal(text="Password", confirm=False, allowedempty=False):
    import getpass
    while True:
        pw = getpass.getpass(text)
        if not pw and not allowedempty:
            print("Cannot be empty!")
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
                print("Not matching!")
    return pw


def pprintOperation(op):
    from bitshares.price import Order, FilledOrder
    if op["op"][0] == 1:
        return str(Order(op["op"][1]))
    if op["op"][0] == 4:
        return str(FilledOrder(op["op"][1]))
    else:
        return json.dumps(op["op"][1], indent=4)
