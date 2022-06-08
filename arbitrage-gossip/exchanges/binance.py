import logging
import aiohttp
import asyncio.exceptions
from datetime import datetime
from typing import Any

from exchanges.base import BaseExchange


class Binance(BaseExchange):
    """Implements monitoring for Binance."""

    """ Binance http api url """
    api = "https://api.binance.com"

    """ Binance websocket api url """
    api_ws = "wss://stream.binance.com:9443/ws"

    def __init__(
        self,
        pair: str,
        timeout: float = 10.0,
        receive_timeout: float = 60.0,
    ) -> None:
        super().__init__(pair.lower(), timeout, receive_timeout)
        logging.info(f"{self.exchange} Initialized with {self.__dict__}")

    async def check_pair_exists(self) -> bool:
        """Check if the pair is offered by Binance."""

        url = f"{self.api}/api/v3/exchangeInfo"
        params = {"symbol": self.pair.upper()}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    logging.debug({"{self.exchange} check_pair_exists response": resp})
                    resp = await resp.json()
                    if (
                        resp["symbols"][0]["symbol"] == self.pair.upper()
                        and resp["symbols"][0]["status"] == "TRADING"
                    ):
                        logging.info(
                            f'{self.exchange} pair "{self.pair}" is offered. MONITORING {self.exchange}'
                        )
                        return True

                logging.warning(
                    f'{self.exchange} pair "{self.pair}" IS NOT offered. NOT MONITORING {self.exchange}.'
                )
                return False

    async def run(self) -> None:
        """Fetch the price from Binance."""

        # don't monitor the exchange if the pair isn't listed
        if not await self.check_pair_exists():
            return

        url = f"{self.api_ws}/{self.pair}@miniTicker"
        while True:
            async with aiohttp.ClientSession() as session:
                try:
                    ws = await session.ws_connect(
                        url,
                        timeout=self.receive_timeout,
                        receive_timeout=self.receive_timeout,
                    )

                    logging.info(
                        f"{self.exchange} Created new Client session and Established a websocket connection towards {self.api_ws}"
                    )

                    while True:
                        try:
                            msg = await ws.receive_json()
                            logging.debug(f"{self.exchange} {msg}")

                            if msg:
                                self.data = {
                                    "price": float(msg["c"]),
                                    "time": datetime.utcfromtimestamp(
                                        msg["E"] / 1000
                                    ).strftime("%Y/%m/%dT%H:%M:%S.%f"),
                                }
                        except TypeError as e:
                            logging.warning(
                                f"{self.exchange} Most likely received a None from the server to close the connection. Restarting."
                            )
                            break
                        except asyncio.exceptions.TimeoutError as e:
                            logging.exception(e)
                            break
                        except (
                            asyncio.exceptions.CancelledError,
                            KeyboardInterrupt,
                        ) as e:
                            logging.warning(
                                f"{self.exchange} Interruption occurred. Exiting."
                            )
                            return
                except KeyboardInterrupt as e:
                    logging.warning("Program Interrupted.. Shutting down.")
                    return
                except BaseException as e:
                    logging.exception(e)
                    await asyncio.sleep(1)
                    continue
