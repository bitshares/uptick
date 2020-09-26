import click
from bitshares.account import Account
from bitshares.amount import Amount
from bitshares.asset import Asset
from bitshares.price import Price
from .decorators import online, unlock
from .main import main, config
from .ui import print_tx, format_tx, print_table, print_message


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


@pool.command()
@click.argument("pool")
@click.argument("sell_amount")
@click.argument("sell_symbol")
@click.argument("buy_amount")
@click.argument("buy_symbol")
@click.option(
    "--account", help="Active account (else use wallet default). " +
    "This account must be owner of the POOL."
)
@click.pass_context
@online
@unlock
def exchange(ctx, pool, sell_amount, sell_symbol, buy_amount, buy_symbol, account):
    """ Exchange assets via a Liquidity Pool.

    POOL: The pool to exchange against. This can be given as a pool id (e.g.
    "1.19.x") or as the share asset symbol or id of the pool.

    SELL_AMOUNT and SELL_SYMBOL: Specifies the amount of asset that will be
    sold into the pool.

    BUY_AMOUNT and BUY_SYMBOL: Specify the MINIMUM amount of asset you wish to
    receive from the pool.  The pool will pay out at its exchange rate (less
    fees) so long as it can deliver this minimum expectation. If it cannot,
    the operation will fail.

    """
    ctx.blockchain.blocking = True
    tx = ctx.blockchain.exchange_with_liquidity_pool(
        pool,
        amount_to_sell=Amount(sell_amount, sell_symbol, blockchain_instance=ctx.bitshares),
        min_to_receive=Amount(buy_amount, buy_symbol, blockchain_instance=ctx.bitshares),
        account=account,
    )
    tx.pop("trx", None)
    print_tx(tx)
    results = tx.get("operation_results", {})
    print("Results: ", results)


@pool.command()
@click.argument("pool")
@click.pass_context
@online
def describe(ctx, pool):
    """ Describe a Liquidity Pool.

    Will give details of a particular liquidity pool, including component
    assets, current price, and fee structure of the pool.

    POOL: The pool to describe. This can be given as a pool id (e.g.
    "1.19.x") or as the share asset symbol or id of the pool.

    """
    # Quite messy, and desires a proper Pool object class.  T.B.D. Someday.
    pool_id = ctx.bitshares._find_liquidity_pool(pool) # ad hoc
    data = ctx.bitshares.rpc.get_object(pool_id)
    if data:
        t = [["Key", "Value"]]
        try:
            orig_data = data
            asset_a = Asset(data.pop("asset_a"), blockchain_instance=ctx.bitshares)
            asset_b = Asset(data.pop("asset_b"), blockchain_instance=ctx.bitshares)
            share_asset = Asset(data.pop("share_asset"), blockchain_instance=ctx.bitshares)
            pool_owner = Account(share_asset["issuer"], blockchain_instance=ctx.bitshares)
            share_dyn = ctx.bitshares.rpc.get_object(share_asset["dynamic_asset_data_id"])
            share_supply = int(share_dyn["current_supply"])
            share_supply = Amount(share_supply/10**share_asset.precision, share_asset)
            amount_a = Amount(int(data.pop("balance_a"))/10**asset_a.precision, asset_a)
            amount_b = Amount(int(data.pop("balance_b"))/10**asset_b.precision, asset_b)
            pool_k = int(data.pop("virtual_value"))/10**(asset_a.precision + asset_b.precision)
            taker_fee = int(data.pop("taker_fee_percent"))/100
            withdrawal_fee = int(data.pop("withdrawal_fee_percent"))/100
            data.pop("id")
            t.append(["Pool Name", "%s"%(share_asset["symbol"])])
            t.append(["Pool Id", "%s"%(pool_id)])
            t.append(["Pool Owner", "%s (%s)"%(pool_owner["name"],pool_owner["id"])])
            t.append(["Asset A", "%s (%s)"%(asset_a["symbol"],asset_a["id"])])
            t.append(["Asset B", "%s (%s)"%(asset_b["symbol"],asset_b["id"])])
            t.append(["",""])
            t.append(["Balance of Asset A", str(amount_a)])
            t.append(["Balance of Asset B", str(amount_b)])
            t.append(["",""])
            t.append(["Outstanding Pool Shares", "%s (%s)"%(str(share_supply),share_asset["id"])])
            t.append(["Pool Invariant (k=xy)", pool_k])
            t.append(["",""])
            t.append(["Nominal Pool Price", Price(base=amount_a, quote=amount_b, blockchain_instance=ctx.bitshares)])
            t.append(["",""])
            t.append(["Price Resilience:",""])
            t.append(["(approximate, w/o fees)",""])
            t.append(["     1% Slippage:", "%s, or %s"%(amount_b*.01,amount_a*.01)])
            t.append(["     5% Slippage:", "%s, or %s"%(amount_b*.05,amount_a*.05)])
            t.append(["    10% Slippage:", "%s, or %s"%(amount_b*.1,amount_a*.1)])
            t.append(["",""])
            t.append(["Exchange Fee", "%0.2f%%"%taker_fee])
            t.append(["Withdrawal Fee", "%0.2f%%"%withdrawal_fee])
        except:
            raise
            t = [["Key", "Value"]]
            data = orig_data
            pass # If schema not what we expected, reset and fall through to sorted list.
        for key in sorted(data):
            value=data[key]
            if isinstance(value, dict) or isinstance(value, list):
                value = format_tx(value)
            t.append([key, value])
        print_table(t)
    else:
        print_message("Could not retrieve pool object", "warning")
