import logging
import aiohttp
import asyncio.exceptions
import json
from datetime import datetime
from typing import Any

from exchanges.base import BaseExchange


class ByBit(BaseExchange):
    """Implements monitoring for ByBit."""

    """ ByBit http api url. """
    api: str = "https://api.bybit.com"

    """ Bybit websocket api url. """
    api_ws: str = "wss://stream.bybit.com/spot/quote/ws/v1"

    def __init__(
        self,
        pair: str,
        timeout: float = 10.0,
        receive_timeout: float = 60.0,
    ) -> None:

        """Monitored pair."""
        self.pair = pair.upper()

        """ Exchange name. """
        self.exchange = self.__class__.__name__

        """ Websocket connection timeout. """
        self.timeout: float = timeout
        self.receive_timeout: float = receive_timeout

        """ Holds all live websocket data. """
        self.data: dict[str, Any] = {}

        """ If pair isn't offered by exchange =False else =True."""
        self.monitor: bool

        logging.info(f"{self.exchange} Initialized with {self.__dict__}")

    async def check_pair_exists(self) -> bool:
        """Check if a pair is offered by the exchange. Returns bool."""

        url = f"{self.api}/v2/public/tickers"
        params = {"symbol": self.pair}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                logging.debug({"{self.exchange} check_pair_exists response": resp})
                resp = await resp.json()
                if resp["ret_code"] == 0:
                    logging.info(
                        f'{self.exchange} pair "{self.pair}" is offered. MONITORING {self.exchange}'
                    )
                    return True

                logging.warning(
                    f'{self.exchange} pair "{self.pair}" IS NOT offered. NOT MONITORING {self.exchange}.'
                )
                return False

    async def run(self) -> None:
        """Run an infinite socket connection if the pair is offered by the exchange"""

        # don't monitor this exchange if the pair isn't offered
        if not self.monitor:
            return

        while True:
            async with aiohttp.ClientSession() as session:
                logging.info(f"{self.exchange} Created new client session.")

                # for some reason bybit sends data of type None every 5 minutes
                # so we handle the TypeError that occurs on ws.receive_json()
                # and immediately establish a new connection
                try:
                    ws = await session.ws_connect(
                        self.api_ws,
                        timeout=self.timeout,
                        receive_timeout=self.receive_timeout,
                    )
                    logging.info(
                        f"{self.exchange} Established a websocket connection towards {self.api_ws}"
                    )

                    await ws.send_str(
                        json.dumps(
                            {
                                "symbol": self.pair,
                                "topic": "realtimes",
                                "event": "sub",
                                "params": {"binary": "false"},
                            }
                        )
                    )

                    while True:
                        try:
                            msg = await ws.receive_json()
                            logging.debug(f"{self.exchange} {msg}")

                            if "data" in msg:
                                self.data = {
                                    # "pair": msg["symbol"],
                                    "price": float(msg["data"][0]["c"]),
                                    "time": datetime.utcfromtimestamp(
                                        msg["data"][0]["t"] / 1000
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
                        except asyncio.exceptions.CancelledError as e:
                            logging.warning(
                                f"{self.exchange} Interruption occurred. Exiting."
                            )
                            return
                except KeyboardInterrupt as e:
                    logging.warning("Program Interrupted.. Shutting down.")
                except BaseException as e:
                    logging.exception(e)
                    continue
