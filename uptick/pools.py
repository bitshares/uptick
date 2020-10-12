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
@click.argument("amount_a", type=float)
@click.argument("symbol_a")
@click.argument("amount_b", type=float)
@click.argument("symbol_b")
@click.option(
    "--account", help="Active account (else use wallet default)."
)
@click.pass_context
@online
@unlock
def deposit(ctx, pool, amount_a, symbol_a, amount_b, symbol_b, account):
    """Stake assets in a Liquidity Pool.

    POOL: The pool to deposit assets into. This can be given as a pool id
    (e.g.  "1.19.x") or as the share asset symbol (or asset id) of the pool's
    share asset.

    AMOUNT's and SYMBOL's: Specifies the amounts of each asset that will be
    deposited into the pool.  The amounts of each asset must be of "equal
    value" according to the pool's current exchange rate (or in other words,
    ratio of AMOUNT_A to AMOUNT_B must be the same as the pool ratio.)  If
    they are not equal-valued, then whichever asset is in excess will be only
    partially deposited and the excess retained by your account.

    In return for your deposit, you will receive a quantity of the pool's
    "share asset" which will represent your stake in the pool and can be used
    to withdraw from the pool at a later date.

    """
    ctx.blockchain.blocking = True
    tx = ctx.blockchain.deposit_into_liquidity_pool(
        pool,
        amount_a=Amount(amount_a, symbol_a, blockchain_instance=ctx.bitshares),
        amount_b=Amount(amount_b, symbol_b, blockchain_instance=ctx.bitshares),
        account=account,
    )
    tx.pop("trx", None)
    print_tx(tx)
    results = tx.get("operation_results", {})
    print("Results: ", results)


@pool.command()
@click.argument("pool")
@click.argument("amount", type=float)
@click.argument("symbol")
@click.option(
    "--account", help="Active account (else use wallet default)."
)
@click.pass_context
@online
@unlock
def withdraw(ctx, pool, amount, symbol, account):
    """Withdraw stake from a Liquidity Pool.

    Redeem shares in a pool for their corresponding fraction of the component
    assets held in the pool, less a withdrawal fee.

    Example: If you hold 10% of the current supply of POOL.SHARE for a pool
    between SOMECOIN and BTS, you can "cash in" your POOL.SHARE for 10% each
    of the pool's holdings of SOMECOIN and BTS (less the withdrawal fee).

    POOL: The pool from which you are withdrawing. This can be given as a pool
    id (e.g.  "1.19.x") or as the share asset symbol (or asset id) of the
    pool's share asset.

    AMOUNT and SYMBOL: These specify the amount of pool share asset that you
    wish to redeem for pool holdings.  (Note: POOL and SYMBOL will be the same
    if you identified the pool by its share asset instead of by its pool id.)

    """
    ctx.blockchain.blocking = True
    tx = ctx.blockchain.withdraw_from_liquidity_pool(
        pool,
        share_amount=Amount(amount, symbol, blockchain_instance=ctx.bitshares),
        account=account,
    )
    tx.pop("trx", None)
    print_tx(tx)
    results = tx.get("operation_results", {})
    print("Results: ", results)


@pool.command()
@click.argument("pool")
@click.argument("sell_amount", type=float)
@click.argument("sell_symbol")
@click.argument("buy_amount", type=float)
@click.argument("buy_symbol")
@click.option(
    "--account", help="Active account (else use wallet default)."
)
@click.pass_context
@online
@unlock
def exchange(ctx, pool, sell_amount, sell_symbol, buy_amount, buy_symbol, account):
    """Exchange assets via a Liquidity Pool.

    POOL: The pool to exchange against. This can be given as a pool id (e.g.
    "1.19.x") or as the share asset symbol (or asset id) of the pool's share
    asset.

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
@click.option(
    "--slip", type=float,
    help = "Add a slippage percent to slippage table."
)
@click.option(
    "--slip-buy", type=float,
    help = "Compute slippage based on buying x% of pool."
)
@click.option(
    "-v", "--verbose", is_flag=True,
    help = "Show some additional pool information if available."
)
@click.pass_context
@online
def describe(ctx, pool, slip, slip_buy, verbose):
    """Describe a Liquidity Pool.

    Gives detailed information about a particular liquidity pool, including
    component assets, share supply, and current exchange rates, including
    slippage estimates to help predict realizable exchange rate based on size
    of trade, and fee structure of the pool.

    POOL: The pool to describe. This can be given as a pool id (e.g.
    "1.19.x") or as the share asset symbol (or asset id) of the pool's share
    asset.

    Note on Slippage Estimates: Estimated trades account for pool fees, but do
    not account for market fees of the traded assets, if any. You may need to
    account for these yourself.

    You can use the --slip option to add a slippage percent to the slippage
    table to estimate outcomes of larger trades.  Slippage percents are based
    on SELLING a percentage quantity of asset into the pool.  To calculate a
    slippage based on BUYING a percentage of the pool, use the --slip-buy
    option.  (The formula is buy_pct = sell_pct/(100% - sell_pct).)

    """
    # Quite messy, and desires a proper Pool object class.  T.B.D. Someday.
    slip_pcts = [0.01, 0.05, 0.10]
    if slip:
        slip_pcts.append(float(slip)/100)
        slip_pcts.sort()
    if slip_buy:
        pct=float(slip_buy)/100
        slip_pcts.append(pct/(1-pct))
        slip_pcts.sort()
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
            if verbose:
                pool_desc = share_asset["options"]["description"]
                if "description" in share_asset:
                    pool_desc = share_asset["description"]
                if isinstance(pool_desc, dict):
                    pool_desc = format_tx(pool_desc)
            # Generate Table:
            t.append(["Pool Name", "%s"%(share_asset["symbol"])])
            if verbose:
                t.append(["Pool Description", pool_desc])
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
            t.append(["Nominal Pool Price (A/B)", Price(base=amount_a, quote=amount_b, blockchain_instance=ctx.bitshares)])
            t.append(["Nominal Pool Price (B/A)", Price(base=amount_b, quote=amount_a, blockchain_instance=ctx.bitshares)])
            t.append(["",""])
            t.append(["Price Resilience:",""])
            def recv(pct):
                return (pct/(1+pct))*((100.0-taker_fee)/100)
            t.append(["",""])
            t.append(["  Selling Asset A:",""])
            t.append(["",""])
            for sl in slip_pcts:
                t.append([
                    "   %4g%% Slippage"%(sl*100),
                    "Sell %s for %s"%(amount_a*sl, amount_b*recv(sl))
                ])
            t.append(["",""])
            t.append(["  Selling Asset B:",""])
            t.append(["",""])
            for sl in slip_pcts:
                t.append([
                    "   %4g%% Slippage"%(sl*100),
                    "Sell %s for %s"%(amount_b*sl, amount_a*recv(sl))
                ])
            t.append(["",""])
            t.append(["  (est. with fees)",""])
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
