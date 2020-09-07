import click
from bitshares.amount import Amount
from .decorators import online, unlock
from .main import main, config
from .ui import print_tx
from bitsharesbase.operations import ticket_type_strings


@main.group()
def ticket():
    """ Commands to create/update voting tickets
    """
    pass


@ticket.command()
@click.argument("target", type=click.Choice(ticket_type_strings[1:]))
@click.argument("amount")
@click.argument("symbol")
@click.option("--account", help="Active account (else use wallet default).")
@click.pass_context
@online
@unlock
def create(ctx, target, amount, symbol, account):
    """ Create a voting ballot.

        Lock a quantity of core token for a period of time for
        vote-weight multiplication.
    """

    ctx.blockchain.blocking = True
    tx = ctx.blockchain.voting_ticket_create(
        target,
        Amount(amount, symbol),
        account
    )
    tx.pop("trx", None)
    print_tx(tx)
    results = tx.get("operation_results", {})
    if results:
        ballot_id = results[0][1]
        print("Your voting ticket id is: {}".format(ballot_id))
        print("Use 'uptick info {}' to monitor your ticket.".format(ballot_id))
