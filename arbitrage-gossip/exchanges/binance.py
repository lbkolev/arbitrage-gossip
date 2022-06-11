import aiohttp
import asyncio.exceptions
import logging as log
from datetime import datetime

from exchanges.base import BaseExchange


class Binance(BaseExchange):
    """Implements monitoring for Binance."""

    """ Binance http api url """
    api = "https://api.binance.com"

    """ Binance websocket api url """
    api_ws = "wss://stream.binance.com:9443/ws"

    def __init__(self, pair: str) -> None:
        super().__init__(pair.lower())
        log.info(f"{self.exchange} Initialized with {self.__dict__}")

    async def _check_pair_exists(self) -> bool:
        """Check if the pair is offered by Binance."""

        url = f"{self.api}/api/v3/exchangeInfo"
        params = {"symbol": self.pair.upper()}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                log.debug({"{self.exchange} _check_pair_exists response": resp})
                if resp.status == 200:
                    resp = await resp.json()
                    if (
                        resp["symbols"][0]["symbol"] == self.pair.upper()
                        and resp["symbols"][0]["status"] == "TRADING"
                    ):
                        log.info(
                            f'{self.exchange} pair "{self.pair}" is offered. MONITORING {self.exchange}'
                        )
                        return True

                log.warning(
                    f'{self.exchange} pair "{self.pair}" is NOT offered. NOT MONITORING {self.exchange}.'
                )
                return False

    async def run(self) -> None:
        """Fetch the price from Binance."""

        # don't monitor the exchange if the pair isn't listed
        if not await self._check_pair_exists():
            return

        url = f"{self.api_ws}/{self.pair}@miniTicker"
        while True:
            async with aiohttp.ClientSession() as session:
                try:
                    ws = await session.ws_connect(url)

                    log.info(
                        f"{self.exchange} Created new Client session and Established a websocket connection towards {self.api_ws}"
                    )

                    while True:
                        try:
                            msg = await ws.receive_json()
                            log.debug(f"{self.exchange} {msg}")

                            # example response
                            # {"e":"24hrMiniTicker","E":1654932552785,"s":"BTCUSDT","c":"29313.50000000","o":"30088.62000000","h":"30184.40000000","l":"28850.00000000","v":"64257.42829000","q":"1891748550.51386060"}
                            self.data = {
                                "price": float(msg["c"]),
                                "time": datetime.utcfromtimestamp(
                                    msg["E"] / 1000
                                ).strftime("%Y/%m/%dT%H:%M:%S.%f"),
                            }
                        except (TypeError, asyncio.exceptions.TimeoutError) as e:
                            log.exception(e)
                            break
                        except (asyncio.exceptions.CancelledError, KeyboardInterrupt):
                            log.warning(
                                f"{self.exchange} Interruption occurred. Exiting."
                            )
                            return
                except BaseException as e:
                    log.exception(e)
                    return
