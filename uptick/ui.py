import sys
from prettytable import PrettyTable, ALL as allBorders


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
        for type_ in ["account_auths", "key_auths"]:
            for authority in account[permission][type_]:
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
