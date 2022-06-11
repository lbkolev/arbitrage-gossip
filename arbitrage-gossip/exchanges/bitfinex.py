import aiohttp
import asyncio.exceptions
import logging as log
from datetime import datetime
import json

from exchanges.base import BaseExchange


class Bitfinex(BaseExchange):
    """Implements monitoring for Bitfinex."""

    """Bitfinex api url"""
    api = "https://api-pub.bitfinex.com"

    """Bitfinex websocket api url"""
    api_ws = "wss://api-pub.bitfinex.com/ws/2"

    def __init__(self, pair: str) -> None:
        # for some reason bitfinex implements USDT as UST
        pair = pair.upper().replace("USDT", "UST")
        super().__init__(pair)
        log.info(f"{self.exchange} Initialized with {self.__dict__}")

    async def _check_pair_exists(self) -> bool:
        """Check if the pair is offered by Bitfinex."""

        # check two pairs, BASE:QUOTE and BASEQUOTE
        pairs = [self.pair.replace("-", ""), self.pair.replace("-", ":")]

        url = f"{self.api}/v2/conf/pub:list:pair:exchange"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                log.debug({"{self.exchange} _check_pair_exists response": resp})
                resp = await resp.json()
                if pairs[0] in resp[0]:
                    log.info(
                        f'{self.exchange} pair "{self.pair}" is offered. MONITORING {self.exchange}'
                    )
                    self.pair = pairs[0]
                    return True
                elif pairs[1] in resp[0]:
                    log.info(
                        f'{self.exchange} pair "{self.pair}" is offered. MONITORING {self.exchange}'
                    )
                    self.pair = pairs[1]
                    return True

                log.warning(
                    f'{self.exchange} pair "{self.pair}" is NOT offered. NOT MONITORING {self.exchange}'
                )
                return False

    async def _subscribe(self, ws) -> bool:
        # sys.stdout.write(f"{self.exchange} SELF.PAIR: {self.pair}")
        await ws.send_str(
            json.dumps(
                {
                    "event": "subscribe",
                    "channel": "ticker",
                    "symbol": self.pair,
                }
            )
        )

        # first response is of the type
        # {'event': 'info', 'version': 2, 'serverId': '10f0969e-4291-4afc-ad35-02c80d847e6f', 'platform ': {'status': 1}}
        # the second gives us indication if we are actually subscribed
        # error looks like {'channel': 'ticker', 'symbol': 'BTCUSTT', 'event': 'error', 'msg': 'symbol: invalid', 'code': 10300, 'pair': 'TCUSTT'}
        # success looks like {'event': 'subscribed', 'channel': 'ticker', 'chanId': 627364, 'symbol': 'tBTCUST', 'pair': 'BTCUST'}
        await ws.receive_json()
        resp = await ws.receive_json()
        if resp["event"] == "subscribed":
            log.debug(f"{self.exchange} Subscribed to {self.pair}")
            return True
        log.warning(f"{self.exchange} Unable to subscribe {resp}")
        return False

    async def run(self) -> None:
        """Fetch the price from Bitfinex."""

        if not await self._check_pair_exists():
            return

        while True:
            async with aiohttp.ClientSession() as session:
                log.debug(f"{self.exchange} Created new client session.")

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
                            log.debug(f"{self.exchange} received: {msg}")
                            # bitfinex sends heartbeat packet every 15 seconds, so we check if it isn't one and then process
                            # example responses:
                            # [318834, [29278, 12.84014315, 29283, 8.850295029999998, -795, -0.0264, 29283, 628.17665028, 30182, 28864]]
                            # [318834, 'hb']
                            if msg[1] != "hb":
                                self.data = {
                                    "price": float(msg[1][6]),
                                    "time": datetime.utcnow().strftime(
                                        "%Y/%m/%dT%H:%M:%S.%f"
                                    ),
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
