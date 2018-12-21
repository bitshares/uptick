import click
from prettytable import PrettyTable
from bitshares.amount import Amount
from bitshares.account import Account
from bitshares.price import Price, Order
from bitshares.vesting import Vesting
from .decorators import onlineChain, unlockWallet, online, unlock
from .main import main
from .ui import print_tx, print_table


@main.command()
@click.argument("account")
@click.pass_context
@online
def vesting(ctx, account):
    """ List accounts vesting balances
    """
    account = Account(account, full=True)
    t = [["vesting_id", "claimable"]]
    for vest in account["vesting_balances"]:
        vesting = Vesting(vest)
        t.append([vesting["id"], str(vesting.claimable)])
    print_table(t)


@main.command()
@click.option("--account", default=None)
@click.argument("vestingid")
@click.argument("amount", default=0)
@click.pass_context
@online
@unlock
def claim(ctx, vestingid, account, amount):
    """ Claim funds from the vesting balance
    """
    vesting = Vesting(vestingid)
    if amount:
        amount = Amount(float(amount), "BTS")
    else:
        amount = vesting.claimable
    print_tx(
        ctx.bitshares.vesting_balance_withdraw(
            vesting["id"], amount=amount, account=vesting["owner"]
        )
    )


@main.command()
@click.option("--account", default=None)
@click.argument("amount", type=float)
@click.argument("symbol", type=str)
@click.pass_context
@online
@unlock
def reserve(ctx, amount, symbol, account):
    """ Reserve/Burn tokens
    """
    print_tx(
        ctx.bitshares.reserve(
            Amount(amount, symbol, bitshares_instance=ctx.bitshares), account=account
        )
    )
