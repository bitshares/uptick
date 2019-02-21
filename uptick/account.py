import sys
import json
import click
from prettytable import PrettyTable
from bitshares.block import Block, BlockHeader
from bitshares.account import Account
from .decorators import onlineChain, unlockWallet
from .ui import print_permissions, pprintOperation, print_table, print_tx
from .main import main, config


@main.command()
@click.pass_context
@onlineChain
@click.argument("foreign_account", required=False, type=str)
@click.option(
    "--account",
    default=config["default_account"],
    type=str,
    help="Account to be modified",
)
@click.option(
    "--permission", default="active", type=str, help="Permission/Role to be modified"
)
@click.option("--threshold", type=int, help="Threshold for the Role")
@click.option("--weight", type=int, help="Weight of the new key/account")
@unlockWallet
def allow(ctx, foreign_account, permission, weight, threshold, account):
    """ Add a key/account to an account's permission
    """
    if not foreign_account:
        from bitsharesbase.account import PasswordKey

        pwd = click.prompt(
            "Password for Key Derivation", hide_input=True, confirmation_prompt=True
        )
        foreign_account = format(
            PasswordKey(account, pwd, permission).get_public(), "BTS"
        )
    print_tx(
        ctx.bitshares.allow(
            foreign_account,
            weight=weight,
            account=account,
            permission=permission,
            threshold=threshold,
        )
    )


@main.command()
@click.pass_context
@onlineChain
@click.argument("foreign_account", type=str)
@click.option(
    "--account",
    default=config["default_account"],
    help="Account to be modified",
    type=str,
)
@click.option(
    "--permission", default="active", help="Permission/Role to be modified", type=str
)
@click.option("--threshold", help="Threshold for the Role", type=int)
@unlockWallet
def disallow(ctx, foreign_account, permission, threshold, account):
    """ Remove a key/account from an account's permission
    """
    print_tx(
        ctx.bitshares.disallow(
            foreign_account, account=account, permission=permission, threshold=threshold
        )
    )


@main.command()
@click.pass_context
@onlineChain
@click.argument("account", nargs=-1)
@click.option("--csv/--table", help="Show output as csv or table", default=False)
@click.option(
    "--type", type=str, help="Only show operations of this type", multiple=True
)
@click.option("--exclude", type=str, help="Exclude certain types", multiple=True)
@click.option("--limit", type=int, help="Limit number of elements", default=15)
@click.option("--raw/--no-raw", default=False)
def history(ctx, account, limit, type, csv, exclude, raw):
    """ Show history of an account
    """
    from bitsharesbase.operations import getOperationNameForId

    t = [["#", "time (block)", "operation", "details"]]

    for a in account:
        account = Account(a, bitshares_instance=ctx.bitshares)
        for b in account.history(limit=limit, only_ops=type, exclude_ops=exclude):
            block = BlockHeader(b["block_num"])
            row = [
                b["id"],
                "%s (%s)" % (block.time(), b["block_num"]),
                "{} ({})".format(getOperationNameForId(b["op"][0]), b["op"][0]),
                pprintOperation(b) if not raw else json.dumps(b, indent=4),
            ]
            t.append(row)
    print_table(t)


@main.command()
@click.pass_context
@onlineChain
@click.argument("to", nargs=1, type=str)
@click.argument("amount", nargs=1, type=float)
@click.argument("asset", nargs=1, type=str)
@click.argument("memo", required=False, type=str, default=None)
@click.option(
    "--account", default=config["default_account"], help="Account to send from"
)
@unlockWallet
def transfer(ctx, to, amount, asset, memo, account):
    """ Transfer assets
    """
    print_tx(ctx.bitshares.transfer(to, amount, asset, memo=memo, account=account))


@main.command()
@click.pass_context
@onlineChain
@click.argument("accounts", nargs=-1)
def balance(ctx, accounts):
    """ Show Account balances
    """
    t = [["Account", "Amount"]]
    for a in accounts:
        account = Account(a, bitshares_instance=ctx.bitshares)
        for b in account.balances:
            t.append([str(a), str(b)])
    print_table(t)


@main.command()
@click.pass_context
@onlineChain
@click.argument("account", nargs=1)
def permissions(ctx, account):
    """ Show permissions of an account
    """
    print_permissions(Account(account))


@main.command()
@click.pass_context
@onlineChain
@click.argument("accountname", nargs=1, type=str)
@click.option(
    "--account",
    default=config["default_account"],
    help="Account to pay the registration fee",
)
@click.option(
    "--password",
    prompt="Account Password",
    hide_input=True,
    confirmation_prompt=True,
    help="Account Password",
)
@unlockWallet
def newaccount(ctx, accountname, account, password):
    """ Create a new account
    """
    print_tx(
        ctx.bitshares.create_account(accountname, registrar=account, password=password)
    )


@main.command()
@click.pass_context
@onlineChain
@click.argument("account", nargs=1, default=config["default_account"], type=str)
@unlockWallet
def upgrade(ctx, account):
    """ Upgrade account
    """
    print_tx(ctx.bitshares.upgrade_account(account))


@main.command()
@click.pass_context
@onlineChain
@click.option(
    "--account",
    nargs=1,
    default=config["default_account"],
    help="Account to clone",
    type=str,
)
@click.argument("account_name", nargs=1, type=str)
@unlockWallet
def cloneaccount(ctx, account_name, account):
    """ Clone an account

        This copies the owner and active permissions as well as the
        options (e.g. votes, memo key)
    """
    from bitsharesbase import transactions, operations

    account = Account(account)
    op = {
        "fee": {"amount": 0, "asset_id": "1.3.0"},
        "registrar": account["id"],
        "referrer": account["id"],
        "referrer_percent": 100,
        "name": account_name,
        "owner": account["owner"],
        "active": account["active"],
        "options": account["options"],
        "extensions": {},
        "prefix": ctx.bitshares.rpc.chain_params["prefix"],
    }
    op = operations.Account_create(**op)
    print_tx(ctx.bitshares.finalizeOp(op, account, "active"))


@main.command()
@click.pass_context
@onlineChain
@click.option("--key", prompt="Memo Key", type=str)
@click.option(
    "--account",
    default=config["default_account"],
    type=str,
    help="Account to be modified",
)
@unlockWallet
def changememokey(ctx, key, account):
    """ Change the memo key of an account
    """
    print_tx(ctx.bitshares.update_memo_key(key, account=account))


@main.command()
@click.pass_context
@onlineChain
@click.argument("whitelist_account", type=str)
@click.option(
    "--account",
    default=config["default_account"],
    type=str,
    help="Account to be modified",
)
@unlockWallet
def whitelist(ctx, whitelist_account, account):
    """ Add an account to a whitelist
    """
    account = Account(account, blockchain_instance=ctx.blockchain)
    print_tx(account.whitelist(whitelist_account))


@main.command()
@click.pass_context
@onlineChain
@click.argument("blacklist_account", type=str)
@click.option(
    "--account",
    default=config["default_account"],
    type=str,
    help="Account to be modified",
)
@unlockWallet
def blacklist(ctx, blacklist_account, account):
    """ Add an account to a blacklist
    """
    account = Account(account, blockchain_instance=ctx.blockchain)
    print_tx(account.blacklist(blacklist_account))


@main.command()
@click.pass_context
@onlineChain
@click.argument("unlist_account", type=str)
@click.option(
    "--account",
    default=config["default_account"],
    type=str,
    help="Account to be modified",
)
@unlockWallet
def unlist(ctx, unlist_account, account):
    """ Remove an account from any list
    """
    account = Account(account, blockchain_instance=ctx.blockchain)
    print_tx(account.nolist(unlist_account))


@main.command()
@click.pass_context
@onlineChain
@click.argument("proxy_account", type=str)
@click.option(
    "--account",
    default=config["default_account"],
    help="Account to be modified",
    type=str,
)
@unlockWallet
def setproxy(ctx, proxy_account, account):
    """ Set the proxy account for an account
    """
    print_tx(ctx.bitshares.set_proxy(proxy_account, account=account))


@main.command()
@click.pass_context
@onlineChain
@click.option(
    "--account",
    default=config["default_account"],
    help="Account to be modified",
    type=str,
)
@unlockWallet
def unsetproxy(ctx, account):
    """ Clear proxy for an account
    """
    print_tx(ctx.bitshares.unset_proxy(account=account))
