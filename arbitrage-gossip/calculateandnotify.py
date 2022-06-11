import asyncio
import logging as log
import random
import time
import os
import signal
from typing import Any

from exchanges.base import BaseExchange
from platforms.base import BasePlatform


class CalculateAndNotify:
    """Calculate the price differences between the exchanges and notify the platforms."""

    def __init__(
        self,
        pair: dict[str, str],
        exchanges: dict[str, BaseExchange],
        platforms: dict[str, BasePlatform],
        threshold: float,
    ) -> None:
        """The monitored pair"""
        self.pair = pair

        """All implemented exchanges"""
        self.exchanges = exchanges

        """All implemented platforms"""
        self.platforms = platforms

        """Threshold for the arbitrage monitor"""
        self.threshold = threshold

        """Exchanges prices"""
        self.exchanges_monitor: dict[str, Any] = {}
        self.exchanges_prices: dict[str, Any] = {}

    async def percentage_change(self, x, y) -> float:
        """Get the percentage change between two values."""
        return (x-y)*100/y

    async def latest_prices(self) -> Any:
        """Get the latest prices from all the exchanges."""
        for name, obj in self.exchanges.items():
            if "price" in obj.data:
                self.exchanges_monitor[name] = {
                    "exchange": obj.exchange,
                    "pair": obj.pair,
                    "price": obj.data["price"],
                    "time": obj.data["time"],
                }
                self.exchanges_prices[name] = obj.data["price"]

        if not self.exchanges_prices:
            return False

        exchange_max = max(self.exchanges_prices, key=self.exchanges_prices.get)
        exchange_min = min(self.exchanges_prices, key=self.exchanges_prices.get)
        # this whole scheme is in case there are N(Where N>1) monitored exchanges and on all of them the price is X
        # there exists a possibility that exchange_min and exchange_max will be the same thing
        # so we shuffle and try again, until they differ
        while True:
            if exchange_min != exchange_max:
                break
            elif (exchange_min == exchange_max) and (len(self.exchanges_prices) == 1):
                break
            elif (exchange_min == exchange_max) and (len(self.exchanges_prices) > 1):
                tmp = list(self.exchanges_prices.items())
                random.shuffle(tmp)
                self.exchanges_prices = dict(tmp)

                exchange_min = min(self.exchanges_prices, key=self.exchanges_prices.get)
                if exchange_min == exchange_max:
                    continue
                else:
                    break
        return {
            "max": {
                "exchange": self.exchanges_monitor[exchange_max]["exchange"],
                "pair": self.exchanges_monitor[exchange_max]["pair"],
                "price": self.exchanges_monitor[exchange_max]["price"],
                "time": self.exchanges_monitor[exchange_max]["time"],
            },
            "min": {
                "exchange": self.exchanges_monitor[exchange_min]["exchange"],
                "pair": self.exchanges_monitor[exchange_min]["pair"],
                "price": self.exchanges_monitor[exchange_min]["price"],
                "time": self.exchanges_monitor[exchange_min]["time"],
            },
        }

    async def run(self):
        """Run the arbitrage monitor."""

        # give the other concurrent functions time to fetch initial websocket data,
        # then begin calculating prices & notifying platforms
        await asyncio.sleep(5)

        prices = await self.latest_prices()
        if prices == False:
            log.error(
                f"Pair {self.pair['merged'].upper()} isn't offered by any of the exchanges. Exiting."
            )
            os.kill(os.getpid(), signal.SIGINT)

        while True:
            prices = await self.latest_prices()
            price_diff = prices["max"]["price"] - prices["min"]["price"]
            price_diff_perc = await self.percentage_change(
                prices["max"]["price"], prices["min"]["price"]
            )

            log.info(f"Highest price {prices['max']}")
            log.info(f"Lowest price {prices['min']}")
            log.info(f"Price difference {price_diff}")
            log.info(f"Price difference in % {price_diff_perc}")

            # notify the platforms
            for platform, obj in self.platforms.items():
                if platform == "twitter":
                    current_time = time.time()
                    if (
                        obj.cooldown + obj.last_reported < current_time
                        and price_diff_perc >= self.threshold
                    ):
                        await obj.notify(
                            self.pair,
                            {
                                "max": prices["max"],
                                "min": prices["min"],
                                "price_diff": price_diff,
                                "price_diff_perc": price_diff_perc,
                            },
                        )
            await asyncio.sleep(1)
