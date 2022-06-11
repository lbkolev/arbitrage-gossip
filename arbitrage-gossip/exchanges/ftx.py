import logging as log
import aiohttp
import asyncio.exceptions
import json
from datetime import datetime
from typing import Any

from exchanges.base import BaseExchange


class FTX(BaseExchange):
    """Implements monitoring for FTX."""

    """ FTX http api url """
    api = "https://ftx.com/api"

    """ FTX websocket api url """
    api_ws = "ws://ftx.com/ws"

    def __init__(self, pair: str) -> None:
        super().__init__(pair.upper())
        log.info(f"{self.exchange} Initialized with {self.__dict__}")

    # should always be called before self.run()
    async def _check_pair_exists(self) -> bool:
        """Check if the pair is listed by FTX."""

        url = f"{self.api}/markets/{self.pair}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                log.debug({"{self.exchange} _check_pair_exists response": resp})
                if resp.status == 200:
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
                    "op": "subscribe",
                    "channel": "ticker",
                    "market": self.pair,
                }
            )
        )

        # first response gives indication if we're subscribed
        # error looks like {'type': 'error', 'code': 404, 'msg': 'No such market: BTCUSDT'}
        # success looks like {'type': 'subscribed', 'channel': 'ticker', 'market': 'BTC/USDT'}
        resp = await ws.receive_json()
        if resp['type'] == 'subscribed':
            log.info(f"{self.exchange} Subscribed to {self.pair}")
            return True

        log.warning(f"{self.exchange} Unable to subscribe {resp}")
        return False

    async def run(self) -> None:
        """Fetch the price from FTX."""

        # don't monitor the exchange if the pair isn't listed
        if not await self._check_pair_exists():
            return

        async with aiohttp.ClientSession() as session:
            log.info(f"{self.exchange} Created new client session.")
            while True:
                try:
                    ws = await session.ws_connect(self.api_ws)
                    log.info(
                        f"{self.exchange} Established a websocket connection towards {self.api_ws}"
                    )

                    if not await self._subscribe(ws):
                        return

                    while True:
                        try:
                            msg = await ws.receive_json()
                            log.debug(f"{self.exchange} {msg}")
                            
                            # example response
                            # {'channel': 'ticker', 'market': 'BTC/USDT', 'type': 'update', 'data': {'bid': 29310.0, 'ask': 29311.0, 'bidSize': 0.7335, 'askSize': 0.2153, 'last': 29310.0, 'time': 1654929638.6974728}}
                            self.data = {
                                "price": float(msg['data']['last']),
                                "time": datetime.utcfromtimestamp(
                                    msg["data"]["time"]
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
