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


@ticket.command()
@click.argument("ticket_id")
@click.argument("target", type=click.Choice(ticket_type_strings))
@click.option(
    "--amount", type=(float, str), default=(None, None),
    help="Amount and  symbol (e.g. 100.0 BTS) of the existing ticket " +
         "amount to update.  If omitted, whole ticket will be updated."
)
@click.option("--account", help="Active account (else use wallet default).")
@click.pass_context
@online
@unlock
def update(ctx, ticket_id, target, amount, account):
    """ Update staking time of a voting ballot.

    Changes the stake-lock duration of a voting ticket. Can update full amount
    of a ticket or a partial amount.  If partial, result is two separate
    tickets, putting optional AMOUNT on the new ticket/time-target while the
    old ticket retains the remainder.  This command can also be used to "free"
    tickets by updating the time target to "liquid" (except for fully-charged
    lock_forever tickets).

    EXAMPLE 1: If ticket 1.18.xxx has 1000 BTS locked for 180 days, you could
    upgrade the entire ticket to a lock_forever ticket with:

    uptick ticket update 1.18.xxx lock_forever

    EXAMPLE 2: If ticket 1.18.yyy has 1500 BTS locked for 180 days, you could
    free a third of it with:

    uptick ticket update --amount 500 BTS 1.18.yyy liquid

    The release of BTS will follow a power-down schedule.

    """

    amount = Amount(*amount) if amount[0] is not None else None
    ctx.blockchain.blocking = True
    tx = ctx.blockchain.voting_ticket_update(
        ticket_id,
        target,
        amount,
        account
    )
    tx.pop("trx", None)
    print_tx(tx)
    results = tx.get("operation_results", {})
    if results:
        results = results[0][1]
        updates = results['updated_objects']
        creates = results['new_objects']
        removes = results['removed_objects']
        monitor = updates + creates
        ticketword={True:"voting tickets", False:"voting ticket"}
        if updates:
            print("Updated existing %s: "%ticketword[len(updates)>1], end='')
            print(*updates, sep=', ')
        if creates:
            print("Created new %s: "%ticketword[len(creates)>1], end='')
            print(*creates, sep=', ')
        if removes:
            print("Removed %s: "%ticketword[len(removes)>1], end='')
            print(*removes, sep=', ')
        if monitor:
            print("Monitor your %s with: uptick info "%ticketword[len(monitor)>1], end='')
            print(*monitor, sep=' ')
