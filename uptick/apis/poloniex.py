from functools import wraps
from flask import (
    Flask,
    jsonify,
    request,
    abort
)
from flask_api import FlaskAPI


app = FlaskAPI(__name__)


def error(e):
    return {"error": e}


@app.route('/public')
def public():
    command = request.args.get('command')

    if command == "returnTicker":
        """
        {"BTC_LTC":{"last":"0.0251","lowestAsk":"0.02589999","highestBid":"0.0251","percentChange":"0.02390438",
        "baseVolume":"6.16485315","quoteVolume":"245.82513926"},"BTC_NXT":{"last":"0.00005730","lowestAsk":"0.00005710",
        "highestBid":"0.00004903","percentChange":"0.16701570","baseVolume":"0.45347489","quoteVolume":"9094"}, ... }
        """
        pass
    elif command == "return24Volume":
        """
        {"BTC_LTC":{"BTC":"2.23248854","LTC":"87.10381314"},"BTC_NXT":{"BTC":"0.981616","NXT":"14145"},
        ... "totalBTC":"81.89657704","totalLTC":"78.52083806"}
        """
        pass
    elif command == "returnOrderBook":
        """
        {"asks":[[0.00007600,1164],[0.00007620,1300], ... ], "bids":[[0.00006901,200],[0.00006900,408], ... ], "isFrozen": 0, "seq": 18849}

        {"BTC_NXT":{"asks":[[0.00007600,1164],[0.00007620,1300], ... ], "bids":[[0.00006901,200],[0.00006900,408], ... ], "isFrozen": 0, "seq": 149},"BTC_XMR":...}

        https://poloniex.com/public?command=returnOrderBook&currencyPair=BTC_NXT&depth=10
        """
        pass
    elif command == "returnTradeHistory":
        """
        [{"date":"2014-02-10 04:23:23","type":"buy","rate":"0.00007600","amount":"140","total":"0.01064"},{"date":"2014-02-10 01:19:37","type":"buy","rate":"0.00007600","amount":"655","total":"0.04978"}, ... ]

        Call: https://poloniex.com/public?command=returnTradeHistory&currencyPair=BTC_NXT&start=1410158341&end=1410499372
        """
        pass
    elif command == "returnChartData":
        """
        [{"date":1405699200,"high":0.0045388,"low":0.00403001,"open":0.00404545,"close":0.00427592,"volume":44.11655644,
        "quoteVolume":10259.29079097,"weightedAverage":0.00430015}, ...]

        Call: https://poloniex.com/public?command=returnChartData&currencyPair=BTC_XMR&start=1405699200&end=9999999999&period=14400
        """
        pass
    elif command == "returnCurrencies":
        """
        {"1CR":{"maxDailyWithdrawal":10000,"txFee":0.01,"minConf":3,"disabled":0},"ABY":{"maxDailyWithdrawal":10000000,"txFee":0.01,"minConf":8,"disabled":0}, ... }
        """
        pass
    elif command == "returnLoanOrders":
        return error("Not available.")
    else:
        return error("Invalid command.")


def run(port):
    """ Run the Webserver/SocketIO and app
    """
    app.run(port=port)
