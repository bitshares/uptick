*******************
Custom Applications
*******************

Uptick is designed in a way that allows you to build your **own
applications** and use the existing infrastructure of pybitshares and
uptick easily. This means that you can use so called **decorators**
to simplify development of your own application.

Example 1: Cancel all orders in a market
----------------------------------------

.. code-block:: python

    from pprint import pprint
    from uptick.decorators import unlock, online
    from uptick.main import main
    from bitshares.market import Market
    import click

    @main.command()
    @click.option("--account", default=None)
    @click.argument("market")
    @click.pass_context
    @online
    @unlock
    def cancelall(ctx, market, account):
        market = Market(market)
        ctx.bitshares.bundle = True
        market.cancel([
            x["id"] for x in market.accountopenorders(account)
        ], account=account)
        pprint(ctx.bitshares.txbuffer.broadcast())


    if __name__ == "__main__":
        main()


Example 2: Spread multiple orders evenly in a market:
-----------------------------------------------------

.. code-block:: python

    from pprint import pprint
    from numpy import linspace
    from uptick.decorators import unlock, online
    from uptick.main import main
    from bitshares.market import Market
    import click


    @main.command()
    @click.option("--account", default=None)
    @click.argument("market")
    @click.argument("side", type=click.Choice(['buy', 'sell']))
    @click.argument("min", type=float)
    @click.argument("max", type=float)
    @click.argument("num", type=float)
    @click.argument("amount", type=float)
    @click.pass_context
    @online
    @unlock
    def spread(ctx, market, side, min, max, num, amount, account):
        market = Market(market)
        ctx.bitshares.bundle = True

        if min < max:
            space = linspace(min, max, num)
        else:
            space = linspace(max, min, num)

        func = getattr(market, side)
        for p in space:
            func(p, amount / float(num), account=account)
        pprint(ctx.bitshares.txbuffer.broadcast())


Decorators
----------
.. automodule:: uptick.decorators
   :members:
   :exclude-members: onlineChain, offlineChain, unlockWallet, online
