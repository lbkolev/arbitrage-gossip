import asyncio
import logging as log
import os
import signal
import time
from typing import Any

from platforms.base import BasePlatform
from calculate import Calculate


class Notify:
    """Notify the platforms about the arbitrage opportunity."""

    def __init__(
        self,
        pair: dict[str, Any],
        calculate: Calculate,
        platforms: dict[str, BasePlatform],
        threshold: float,
    ) -> None:
        """The monitored pair"""
        self.pair = pair

        """Object through which the arbitrage opportunity is calculated"""
        self.calculate = calculate

        """All implemented platforms"""
        self.platforms = platforms

        """Threshold for the arbitrage monitor"""
        self.threshold = threshold

    async def run(self) -> None:
        # give the other concurrent functions time to fetch initial websocket data,
        # then begin calculating prices & notifying platforms
        await asyncio.sleep(10)

        prices = await self.calculate.latest_prices()

        if prices == False:
            log.error("No prices found")
            os.kill(os.getpid(), signal.SIGTERM)

        while True:
            prices = await self.calculate.latest_prices()
            price_diff = prices["max"]["price"] - prices["min"]["price"]
            price_diff_perc = await self.calculate.percentage_change(
                prices["max"]["price"], prices["min"]["price"]
            )

            log.info(f"Highest price {prices['max']}")
            log.info(f"Lowest price {prices['min']}")
            log.info(f"Price difference {price_diff}")
            log.info(f"Price difference in % {price_diff_perc}")

            # notify the platforms
            for platform, obj in self.platforms.items():
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
