import click
from bitshares.amount import Amount
from .decorators import online, unlock
from .main import main, config
from .ui import print_tx


@main.group()
def htlc():
    pass


@htlc.command()
@click.argument("to")
@click.argument("amount")
@click.argument("symbol")
@click.option(
    "--secret", prompt="Redeem Password", hide_input=True, confirmation_prompt=True
)
@click.option(
    "--hash", type=click.Choice(["ripemd160", "sha1", "sha256"]), default="ripemd160"
)
@click.option("--account")
@click.option("--expiration", default=60 * 60)
@click.pass_context
@online
@unlock
def create(ctx, to, amount, symbol, secret, hash, account, expiration):
    """ Create an HTLC contract
    """
    ctx.blockchain.blocking = True
    tx = ctx.blockchain.htlc_create(
        Amount(amount, symbol),
        to,
        secret,
        hash_type=hash,
        expiration=expiration,
        account=account,
    )
    tx.pop("trx", None)
    print_tx(tx)
    results = tx.get("operation_results", {})
    if results:
        htlc_id = results[0][1]
        print("Your htlc_id is: {}".format(htlc_id))


@htlc.command()
@click.argument("htlc_id")
@click.option("--account")
@click.option(
    "--secret", prompt="Redeem Password", hide_input=True, confirmation_prompt=False
)
@click.pass_context
@online
@unlock
def redeem(ctx, htlc_id, secret, account):
    """ Redeem an HTLC contract
    """
    print_tx(ctx.blockchain.htlc_redeem(htlc_id, secret, account=account))
