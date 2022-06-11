import aiohttp
import asyncio.exceptions
import logging as log
from datetime import datetime
import json
import time

from exchanges.base import BaseExchange


class KuCoin(BaseExchange):
    """Implements monitoring for KuCoin."""

    """ Kucoin http api url  """
    api = "https://api.kucoin.com"

    def __init__(self, pair: str) -> None:
        super().__init__(pair.upper())
        log.info(f"{self.exchange} Initialized with {self.__dict__}")

    async def _check_pair_exists(self) -> bool:
        """Check if the pair is offered by KuCoin."""
        url = f"{self.api}/api/v1/symbols"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                log.debug({"{self.exchange} _check_pair_exists response": resp})
                resp = await resp.json()
                for pairs in resp["data"]:
                    if pairs["symbol"] == self.pair and pairs["enableTrading"] == True:
                        log.info(
                            f'{self.exchange} pair "{self.pair}" is offered. MONITORING {self.exchange}'
                        )
                        return True

                    if pairs["symbol"] == self.pair and pairs["enableTrading"] == False:
                        log.warning(
                            f'{self.exchange} pair "{self.pair}" is currently disabled. NOT MONITORING {self.exchange}'
                        )
                        return False

                log.warning(
                    f'{self.exchange} pair "{self.pair}" is NOT offered. NOT MONITORING {self.exchange}'
                )
                return False

    async def _subscribe(self, ws) -> bool:
        await ws.send_str(
            json.dumps(
                {
                    "id": time.time(),
                    "type": "subscribe",
                    "topic": f"/market/ticker:{self.pair}",
                    "privateChannel": False,
                    "response": True,
                }
            )
        )

        # kucoin's first response is a welcome message, the second response one gives indication if the connection is successful
        # first response {'id': 'YTlBdGSzpo', 'type': 'welcome'}
        # second response success {'id': '1654933542.5331', 'type': 'ack'}
        # second response failure {'id': '1654933524.5110245', 'type': 'error', 'code': 404, 'data': 'topic /market/ticker:BTC-USD is not found'}
        await ws.receive_json()
        resp = await ws.receive_json()
        if resp["type"] == "ack":
            log.debug(f"{self.exchange} Subscribed to {self.pair}")
            return True

        log.warning(f"{self.exchange} Unable to subscribe {resp}")
        return False

    # https://docs.kucoin.com/#apply-connect-token
    # 'make request as follows to obtain the server list and temporary public token'
    async def _get_api_ws_and_token(self):
        """Get the websocket url and the ping interval."""
        url = f"{self.api}/api/v1/bullet-public"
        async with aiohttp.ClientSession() as session:
            async with session.post(url) as resp:
                resp = await resp.json()

                if int(resp["code"]) == 200000:
                    api_ws = resp["data"]["instanceServers"][0]["endpoint"]
                    token = resp["data"]["token"]

                    log.debug(f"{self.exchange} Kucoin ws url: {api_ws}?token={token}")

                    return f"{api_ws}?token={token}"

                log.warning(
                    f"{self.exchange} Unable to get ws url and token. NOT MONITORING {self.exchange}"
                )
                return False

    async def run(self) -> None:
        """Fetch the price from KuCoin."""

        # don't monitor the exchange if the pair isn't listed
        if not await self._check_pair_exists():
            return

        async with aiohttp.ClientSession() as session:
            log.debug(f"{self.exchange} Created new client session.")
            while True:
                api_ws = await self._get_api_ws_and_token()

                try:
                    ws = await session.ws_connect(api_ws)
                    log.debug(
                        f"{self.exchange} Established a websocket connection towards {api_ws}"
                    )
                    if not await self._subscribe(ws):
                        return
                    while True:
                        try:
                            # example response:
                            # {'type': 'message', 'topic': '/market/ticker:ETH-USDT', 'subject': 'trade.ticker', 'data': {'bestAsk': '1669.15', 'bestAskSize': '16.0276667', 'bestBid': '1669.14', 'bestBidSize': '5.1395149', 'price': '1669.15', 'sequence': '1629182000135', 'size': '0.0017103', 'time': 1654934466343}}
                            msg = await ws.receive_json()
                            log.debug(f"{self.exchange} {msg}")
                            self.data = {
                                "price": float(msg["data"]["price"]),
                                "time": datetime.utcfromtimestamp(
                                    msg["data"]["time"] / 1000
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
