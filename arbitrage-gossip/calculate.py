import random
from typing import Any

from exchanges.base import BaseExchange

class Calculate:
    """"Calculate the price differences between the exchanges."""

    def __init__(self, exchanges: dict[str, BaseExchange]) -> None:
        """All implemented exchanges"""
        self.exchanges = exchanges

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