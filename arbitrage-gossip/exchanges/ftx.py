import logging
import aiohttp
import asyncio.exceptions
import json
from datetime import datetime
from typing import Any

from exchanges.base import BaseExchange


class FTX(BaseExchange):
    """Implements monitoring for FTX."""

    """ FTX http api url. """
    api: str = "https://ftx.com/api"

    """ FTX websocket api url. """
    api_ws: str = "ws://ftx.com/ws"

    def __init__(
        self,
        pair,
        timeout: float = 10.0,
        receive_timeout: float = 60.0,
    ) -> None:

        """Monitored pair."""
        self.pair = pair.upper()

        """ Exchange name. """
        self.exchange = self.__class__.__name__

        """ Websocket conenction timeout. """
        self.timeout: float = timeout
        self.receive_timeout: float = receive_timeout

        """ Holds all live websocket data. """
        self.data: dict[str, Any] = {}

        """ If pair isn't offered by exchange =False else =True """
        self.monitor = False

        logging.info(f"{self.exchange} Initialized with {self.__dict__}")

    # should always be called before self.run()
    async def check_pair_exists(self) -> bool:
        """Check if a pair is offered by the exchange. Returns bool."""

        url = f"{self.api}/markets/{self.pair}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                logging.debug({"{self.exchange} check_pair_exists response": resp})
                if resp.status == 200:
                    logging.info(
                        f'{self.exchange} pair "{self.pair}" is offered. MONITORING {self.exchange}'
                    )
                    return True

                logging.warning(
                    f'{self.exchange} pair "{self.pair}" IS NOT offered. NOT MONITORING {self.exchange}.'
                )
                return False

    async def run(self) -> None:
        """Run an infinite socket connection if the pair is offered by the exchange."""

        # don't monitor this exchange if the pair isn't offered
        if not self.monitor:
            return

        while True:
            async with aiohttp.ClientSession() as session:
                logging.info(f"{self.exchange} Created new client session.")

                try:
                    ws = await session.ws_connect(
                        self.api_ws,
                        timeout=self.receive_timeout,
                        receive_timeout=self.receive_timeout,
                    )
                    logging.info(
                        f"{self.exchange} Established a websocket connection towards {self.api_ws}"
                    )

                    await ws.send_str(
                        json.dumps(
                            {
                                "op": "subscribe",
                                "channel": "ticker",
                                "market": self.pair,
                            }
                        )
                    )

                    while True:
                        try:
                            msg = await ws.receive_json()
                            logging.debug(f"{self.exchange} {msg}")

                            if "data" in msg:
                                self.data = {
                                    # "pair": msg["market"],
                                    "price": float(
                                        (msg["data"]["bid"] + msg["data"]["ask"]) / 2
                                    ),
                                    "time": datetime.utcfromtimestamp(
                                        msg["data"]["time"]
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
                    await asyncio.sleep(1)
                    continue
