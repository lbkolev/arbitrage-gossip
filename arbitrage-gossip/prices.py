import asyncio
import logging
import random
import time
import os
import signal

from notify.twitter import Twitter


def get_prices(exchanges):
    exchanges_monitor = {}
    exchanges_prices = {}
    logging.getLogger()

    for name, init in exchanges.items():
        if init.monitor and "price" in init.data:
            exchanges_monitor[name] = {
                "exchange": init.exchange,
                "pair": init.pair,
                "price": init.data["price"],
                "time": init.data["time"],
            }
            exchanges_prices[name] = init.data["price"]

    if not exchanges_prices:
        return False
    #    logging.info(f"monitor exchanges: {exchanges_monitored}")
    #    logging.info(f"Exchanges prices: {exchanges_prices}")

    exchange_max = max(exchanges_prices, key=exchanges_prices.get)
    exchange_min = min(exchanges_prices, key=exchanges_prices.get)

    # this whole scheme is in case there are N(N!=1) monitored exchanges and on all of them the price is X
    # there exists a possibility that exchange_min and exchange_max will be the same thing
    # so we shuffle and try again, until they differ
    while True:
        if exchange_min != exchange_max:
            break
        elif (exchange_min == exchange_max) and (len(exchanges_prices) == 1):
            break
        elif (exchange_min == exchange_max) and (len(exchanges_prices) > 1):
            tmp = list(exchanges_prices.items())
            random.shuffle(tmp)
            exchanges_prices = dict(tmp)

            exchange_min = min(exchanges_prices, key=exchanges_prices.get)
            if exchange_min == exchange_max:
                continue
            else:
                break

    return {
        "max": {
            "exchange": exchanges_monitor[exchange_max]["exchange"],
            "pair": exchanges_monitor[exchange_max]["pair"],
            "price": exchanges_monitor[exchange_max]["price"],
            "time": exchanges_monitor[exchange_max]["time"],
        },
        "min": {
            "exchange": exchanges_monitor[exchange_min]["exchange"],
            "pair": exchanges_monitor[exchange_min]["pair"],
            "price": exchanges_monitor[exchange_min]["price"],
            "time": exchanges_monitor[exchange_min]["time"],
        },
    }


"""
    Log the prices and if there's too big of a disrepancy - report it in twitter
"""


async def run(exchanges, pair, threshold, report_to, cooldown):

    # get the global logger
    logging.getLogger()

    # give the other concurrent functions time to fetch initial websocket data,
    # then calculate price differences
    await asyncio.sleep(5)

    # initialize twitter object
    twitter = Twitter(cooldown)

    prices = get_prices(exchanges)
    if prices == False:
        logging.error(
            f"Pair {pair['merged'].upper()} isn't offered by any of the exchanges. Exiting."
        )
        os.kill(os.getpid(), signal.SIGINT)
    # elif prices['max']['exchange'] == prices['min']['exchange']:
    #    logging.error(f"Pair {pair['merged']} is offered only by {prices['min']['exchange']}. There's nothing to compare it with. Exiting.")
    #    os.kill(os.getpid(), signal.SIGINT)

    while True:
        prices = get_prices(exchanges)
        price_diff = prices["max"]["price"] - prices["min"]["price"]
        price_diff_perc = (
            (prices["max"]["price"] - prices["min"]["price"])
            / ((prices["max"]["price"] + prices["min"]["price"]) / 2)
            * 100
        )

        logging.info(f"Highest price {prices['max']}")
        logging.info(f"Lowest price {prices['min']}")
        logging.info(f"Price difference {price_diff}")
        logging.info(f"Price difference in % {price_diff_perc}")

        for platform in report_to:
            if platform == "twitter":
                # notify twitter
                current_time = time.time()
                if (
                    twitter.cooldown + twitter.last_reported < current_time
                    and price_diff_perc >= threshold
                ):
                    await twitter.notify(
                        pair,
                        {
                            "max": prices["max"],
                            "min": prices["min"],
                            "price_diff": price_diff,
                            "price_diff_perc": price_diff_perc,
                        },
                    )
        await asyncio.sleep(1)
