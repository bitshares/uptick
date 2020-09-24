import click
from bitshares.amount import Amount
from .decorators import online, unlock
from .main import main, config
from .ui import print_tx


@main.group()
def pool():
    """ Liquidity pool commands
    """
    pass


@pool.command()
@click.argument("asset_a")
@click.argument("asset_b")
@click.argument("share_asset")
@click.argument("taker_fee", type=float)
@click.argument("withdrawal_fee", type=float)
@click.option(
    "--account", help="Active account (else use wallet default). " +
    "This account must be owner of the SHARE_ASSET."
)
@click.pass_context
@online
@unlock
def create(ctx, asset_a, asset_b, share_asset, taker_fee, withdrawal_fee, account):
    """ Create a new Liquidity Pool.

    ASSET_A, ASSET_B: These are the assets to be traded in the
    pool. Can be symbols or ids. Note that ASSET_A should be the one
    that has the lowest-numbered asset id.

    SHARE_ASSET: This is the asset that represents a share in the pool
    for pool stakers. This asset must be a UIA and have zero supply in
    order to bind it to the pool at creation, and you must be the
    owner of this asset.

    TAKER_FEE: This is the fee percent taken by the pool on exchanges
    made via the pool.  Expressed as a percent from 0.00 to 100.00,
    where "1%" is expressed as 1.00.

    WITHDRAWAL_FEE: This is the fee percent taken by the pool on withdrawal
    of stake from the pool.  Expressed as a percent from 0.00 to 100.00,
    where "1%" is expressed as 1.00.

    """
    ctx.blockchain.blocking = True
    tx = ctx.blockchain.create_liquidity_pool(
        asset_a,
        asset_b,
        share_asset,
        taker_fee,
        withdrawal_fee,
        account=account,
    )
    tx.pop("trx", None)
    print_tx(tx)
    results = tx.get("operation_results", {})
    print("Results: ", results)


@pool.command()
@click.argument("pool")
@click.option(
    "--account", help="Active account (else use wallet default). " +
    "This account must be owner of the POOL."
)
@click.pass_context
@online
@unlock
def delete(ctx, pool, account):
    """ Delete a Liquidity Pool.

    POOL: The pool to be deleted. This can be given as a pool id (e.g.
    "1.19.x") or as the share asset symbol or id of the pool.

    Note the pool must be empty (no balance of either asset) in order to
    delete it.

    """
    ctx.blockchain.blocking = True
    tx = ctx.blockchain.delete_liquidity_pool(
        pool,
        account=account,
    )
    tx.pop("trx", None)
    print_tx(tx)
    results = tx.get("operation_results", {})
    print("Results: ", results)
