from functools import wraps
from flask import Flask, jsonify, request, abort
from flask_api import FlaskAPI


app = FlaskAPI(__name__)
ctx = None


def error(e):
    return {"error": e}


def marketstr(market):
    return "%s_%s" % (market["base"], market["quote"])


@app.route("/public")
def public():
    command = request.args.get("command")

    if command == "returnTicker":
        r = {}
        for pair in ctx.pairs:
            market = Market(pair, bitshares_instance=ctx.bitshares)
            mstr = marketstr(market)
            ticker = market.ticker()
            r[mstr] = {
                "last": ticker["last"],
                "lowestAsk": ticker["lowestAsk"],
                "highestBid": ticker["highestBid"],
                "percentChange": ticker["percentChange"],
                "baseVolume": ticker["baseVolume"],
                "quoteVolume": ticker["quoteVolume"],
            }
        return r

    elif command == "return24Volume":
        r = {}
        total = {}
        for pair in ctx.pairs:
            market = Market(pair, bitshares_instance=ctx.bitshares)
            mstr = marketstr(market)
            ticker = market.ticker()
            base = market["base"]["symbol"]
            quote = market["quote"]["symbol"]
            total["base"] = total.get("base", 0) + ticker["baseVolume"]
            total["quote"] = total.get("quote", 0) + ticker["quoteVolume"]
            r[mstr] = {base: ticker["baseVolume"], quote: ticker["quoteVolume"]}
        for symbol, value in total.items():
            r["total%s" % symbol] = value
        return r

    elif command == "returnOrderBook":
        """
        https://poloniex.com/public?command=returnOrderBook&currencyPair=BTC_NXT&depth=10
        """

        """
        {"asks":[[0.00007600,1164],[0.00007620,1300], ... ], "bids":[[0.00006901,200],[0.00006900,408], ... ], "isFrozen": 0, "seq": 18849}

        {"BTC_NXT":{"asks":[[0.00007600,1164],[0.00007620,1300], ... ], "bids":[[0.00006901,200],[0.00006900,408], ... ], "isFrozen": 0, "seq": 149},"BTC_XMR":...}

        """
        pass
    elif command == "returnTradeHistory":
        """
        Call: https://poloniex.com/public?command=returnTradeHistory&currencyPair=BTC_NXT&start=1410158341&end=1410499372
        """

        """
        [{"date":"2014-02-10 04:23:23","type":"buy","rate":"0.00007600","amount":"140","total":"0.01064"},{"date":"2014-02-10 01:19:37","type":"buy","rate":"0.00007600","amount":"655","total":"0.04978"}, ... ]
        """
        pass
    elif command == "returnChartData":
        """
        Call: https://poloniex.com/public?command=returnChartData&currencyPair=BTC_XMR&start=1405699200&end=9999999999&period=14400
        """

        """
        [{"date":1405699200,"high":0.0045388,"low":0.00403001,"open":0.00404545,"close":0.00427592,"volume":44.11655644,
        "quoteVolume":10259.29079097,"weightedAverage":0.00430015}, ...]
        """
        pass
    elif command == "returnCurrencies":
        r = {}
        for pair in ctx.pairs:
            market = Market(pair, bitshares_instance=ctx.bitshares)
            for symbol in [market["base"], market["quote"]]:
                r[symbol] = {
                    "maxDailyWithdrawal": None,
                    "txFee": "standard transfer fee",
                    "minConf": None,
                    "disabled": False,
                }
        for symbol, value in total.items():
            r["total%s" % symbol] = value
        return r
        """
        {"1CR":{"maxDailyWithdrawal":10000,"txFee":0.01,"minConf":3,"disabled":0},"ABY":{"maxDailyWithdrawal":10000000,"txFee":0.01,"minConf":8,"disabled":0}, ... }
        """
        pass
    elif command == "returnLoanOrders":
        return error("Not available.")
    else:
        return error("Invalid command.")


def run(context, port):
    """ Run the Webserver/SocketIO and app
    """
    global ctx
    ctx = context
    app.run(port=port)
