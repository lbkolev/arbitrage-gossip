import logging
import aiohttp
import asyncio.exceptions
import json, gzip
from datetime import datetime
from typing import Any

from exchanges.base import BaseExchange


class Huobi(BaseExchange):
    """Implements monitoring for Huobi."""

    """ Huobi http api url. """
    api: str = "https://api.huobi.pro"

    """ Huobi websocket api url. """
    api_ws: str = "wss://api.huobi.pro/ws"

    def __init__(
        self,
        pair: str,
        timeout: float = 10.0,
        receive_timeout: float = 60.0,
    ) -> None:
        """Monitored pair."""
        self.pair = pair.lower()

        """ Exchange name. """
        self.exchange = self.__class__.__name__

        """ Websocket connection timeout. """
        self.timeout: float = timeout
        self.receive_timeout: float = receive_timeout

        """ Holds all live websocket data. """
        self.data: dict[str, Any] = {}

        """ If pair isn't offered by exchange =False else =True."""
        self.monitor = False

        logging.info(f"{self.exchange} Initialized with {self.__dict__}")

    async def check_pair_exists(self) -> bool:
        """Check if a pair is offered by the exchange. Returns bool."""

        url: str = f"{self.api}/v2/settings/common/symbols/"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                logging.info({"{self.exchange} check_pair_exists response": resp})
                resp = await resp.json()
                for symbol in resp["data"]:
                    if symbol["sc"] == self.pair and symbol["state"] == "online":
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
                try:
                    ws: aiohttp.ClientWebSocketResponse = await session.ws_connect(
                        self.api_ws,
                        timeout=self.receive_timeout,
                        receive_timeout=self.receive_timeout,
                        heartbeat=5.0,
                    )

                    logging.info(
                        f"{self.exchange} Created new Client session and Established a websocket connection towards {self.api_ws}"
                    )

                    await ws.send_str(
                        json.dumps(
                            {
                                "sub": f"market.{self.pair}.ticker",
                            }
                        )
                    )

                    while True:
                        try:
                            raw_msg = await ws.receive_bytes()
                            msg: str = json.loads(gzip.decompress(raw_msg).decode())
                            logging.debug(f"{self.exchange} {msg}")

                            if "tick" in msg:
                                self.data = {
                                    "price": msg["tick"]["lastPrice"],
                                    "time": datetime.utcfromtimestamp(
                                        msg["ts"] / 1000
                                    ).strftime("%Y/%m/%dT%H:%M:%S.%f"),
                                }

                        except TypeError as e:
                            logging.warning(
                                f"{self.exchange} Most likely received a None from the server to close the connection. Restarting."
                            )
                            # await ws.close()
                            break
                        except asyncio.exceptions.TimeoutError as e:
                            logging.exception(e)
                            # await ws.close()
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
