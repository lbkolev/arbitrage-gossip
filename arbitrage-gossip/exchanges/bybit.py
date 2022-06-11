import aiohttp
import asyncio.exceptions
import logging as log
from datetime import datetime
import json

from exchanges.base import BaseExchange


class ByBit(BaseExchange):
    """Implements monitoring for ByBit."""

    """ ByBit http api url """
    api = "https://api.bybit.com"

    """ Bybit websocket api url """
    api_ws = "wss://stream.bybit.com/spot/quote/ws/v1"

    def __init__(self, pair: str) -> None:
        super().__init__(pair.upper())
        log.info(f"{self.exchange} Initialized with {self.__dict__}")

    async def _check_pair_exists(self) -> bool:
        """Check if the pair is offered by ByBit."""

        url = f"{self.api}/v2/public/tickers"
        params = {"symbol": self.pair}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                log.debug({"{self.exchange} _check_pair_exists response": resp})
                resp = await resp.json()
                if resp["ret_code"] == 0:
                    log.info(
                        f'{self.exchange} pair "{self.pair}" is offered. MONITORING {self.exchange}'
                    )
                    return True

                log.warning(
                    f'{self.exchange} pair "{self.pair}" is NOT offered. NOT MONITORING {self.exchange}.'
                )
                return False

    async def _subscribe(self, ws) -> bool:
        await ws.send_str(
            json.dumps(
                {
                    "event": "sub",
                    "topic": "realtimes",
                    "params": {"binary": "false"},
                    "symbol": self.pair,
                }
            )
        )

        resp = await ws.receive_json()
        # bybit returns code only if there's a problem, else it directly returns the response
        # examples for fail
        # {'code': '-100010', 'desc': 'Invalid Symbols!'}
        # {'code': '-10002', 'desc': 'Invalid event!'}
        # example for success {'symbol': 'BTCUSDT', 'symbolName': 'BTCUSDT', 'topic': 'realtimes', 'params': {'realtimeInterval': '24h', 'binary': 'false'}, 'data': [{'t': 1654927909198, 's': 'BTCUSDT', 'sn': 'BTCUSDT', 'c': '29298.76', 'h': '30234.91', 'l': '28855.01', 'o': '30169.02', 'v': '3915.612362', 'qv': '115172990.1827463', 'm': '-0.0288', 'e': 301}], 'f': True, 'sendTime': 1654927911193}

        if "code" not in resp:
            log.debug(f"{self.exchange} Subscribed to websocket.")
            return True

        log.warning(f"{self.exchange} Unable to subscribe {resp}")
        return False

    async def run(self) -> None:
        """Fetch the price from ByBit."""

        # don't monitor the exchange if the pair isn't listed
        if not await self._check_pair_exists():
            return

        async with aiohttp.ClientSession() as session:
            log.debug(f"{self.exchange} Created new client session.")
            while True:
                try:
                    ws = await session.ws_connect(self.api_ws)
                    log.debug(
                        f"{self.exchange} Established a websocket connection towards {self.api_ws}"
                    )

                    if not await self._subscribe(ws):
                        return
                    while True:
                        try:
                            msg = await ws.receive_json()
                            log.debug(f"{self.exchange} {msg}")

                            # example response:
                            # {'symbol': 'BTCUSDT', 'symbolName': 'BTCUSDT', 'topic': 'realtimes', 'params': {'realtimeInterval': '24h', 'binary': 'false'}, 'data': [{'t': 1654935180037, 's': 'BTCUSDT', 'sn': 'BTCUSDT', 'c': '29259.04', 'h': '30180.58', 'l': '28855.01', 'o': '30065.01', 'v': '3738.712793', 'qv': '109807074.56801432', 'm': '-0.0268', 'e': 301}], 'f': False, 'sendTime': 1654935180324}
                            self.data = {
                                "price": float(msg["data"][0]["c"]),
                                "time": datetime.utcfromtimestamp(
                                    msg["data"][0]["t"] / 1000
                                ).strftime("%Y/%m/%dT%H:%M:%S.%f"),
                            }
                        except (TypeError, asyncio.exceptions.TimeoutError) as e:
                            log.debug(str(e))
                            break
                        except (asyncio.exceptions.CancelledError, KeyboardInterrupt):
                            log.warning(
                                f"{self.exchange} Interruption occurred. Exiting."
                            )
                            return
                except BaseException as e:
                    log.exception(e)
                    await asyncio.sleep(0.3)
                    continue
