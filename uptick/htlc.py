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
    "--type", type=click.Choice(["ripemd160", "sha1", "sha256", "hash160"]),
    default="sha256", prompt="Hash algorithm", show_default=True,
    help="Hash algorithm"
)
@click.option(
    "--hash", prompt="Hash (hex string)", hide_input=False, confirmation_prompt=True,
    help="Hash value as string of hex digits"
)
@click.option(
    "--expiration", default=60 * 60, prompt="Expiration (seconds)",
    help="Duration of HTLC in seconds"
)
@click.option(
    "--length", help="Length of PREIMAGE (not of hash). Generally OK " +
    "to leave this as 0 for unconstrained.", default=0, show_default=True
)
@click.option("--account")
@click.pass_context
@online
@unlock
def create(ctx, to, amount, symbol, type, hash, expiration, length, account):
    """ Create an HTLC contract from a hash and lock-time
    """
    ctx.blockchain.blocking = True
    tx = ctx.blockchain.htlc_create(
        Amount(amount, symbol),
        to,
        hash_type=type,
        hash_hex=hash,
        expiration=expiration,
        account=account,
        preimage_length=length
    )
    tx.pop("trx", None)
    print_tx(tx)
    results = tx.get("operation_results", {})
    if results:
        htlc_id = results[0][1]
        print("Your htlc_id is: {}".format(htlc_id))


@htlc.command()
@click.argument("to")
@click.argument("amount")
@click.argument("symbol")
@click.option(
    "--type", type=click.Choice(["ripemd160", "sha1", "sha256", "hash160"]),
    default="sha256", prompt="Hash algorithm", show_default=True,
    help="Hash algorithm"
)
@click.option(
    "--secret", prompt="Redeem Password", hide_input=True, confirmation_prompt=True,
    help="Ascii-text preimage"
)
@click.option("--expiration", default=60 * 60, prompt="Expiration (seconds)",
    help="Duration of HTLC in seconds"
)
@click.option(
    "--length", help="Length of PREIMAGE (not of hash). Generally OK " +
    "to leave this as 0 for unrestricted. If non-zero, must match length " +
    "of provided preimage", default=0, show_default=True
)
@click.option("--account")
@click.pass_context
@online
@unlock
def create_from_secret(ctx, to, amount, symbol, type, secret, expiration,
                       length, account):
    """Create an HTLC contract from a secret preimage

    If you are the party choosing the preimage, this version of
    htlc_create will compute the hash for you from the supplied
    preimage, and create the HTLC with the resulting hash.
    """
    if length != 0 and length != len(secret):
        raise ValueError("Length must be zero or agree with actual preimage length")

    ctx.blockchain.blocking = True
    tx = ctx.blockchain.htlc_create(
        Amount(amount, symbol),
        to,
        preimage=secret,
        preimage_length=length,
        hash_type=type,
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
@click.option(
    "--secret", prompt="Redeem Password", hide_input=False, confirmation_prompt=False,
    type=str, help="The preimage, as ascii-text, unless --hex is passed"
)
@click.option(
    "--hex", is_flag=True, help="Interpret preimage as hex-encoded bytes"
)
@click.option("--account")
@click.pass_context
@online
@unlock
def redeem(ctx, htlc_id, secret, hex, account):
    """ Redeem an HTLC contract by providing preimage
    """
    encoding = "hex" if hex else "utf-8"
    print_tx(ctx.blockchain.htlc_redeem(htlc_id, secret, encoding=encoding,
                                        account=account)
    )
