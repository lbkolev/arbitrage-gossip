import aiohttp
import asyncio.exceptions
import logging as log
from datetime import datetime
import json, gzip

from exchanges.base import BaseExchange


class Huobi(BaseExchange):
    """Implements monitoring for Huobi."""

    """ Huobi http api url """
    api = "https://api.huobi.pro"

    """ Huobi websocket api url """
    api_ws = "wss://api.huobi.pro/ws"

    def __init__(self, pair: str) -> None:
        super().__init__(pair.lower())
        log.info(f"{self.exchange} Initialized with {self.__dict__}")

    async def _check_pair_exists(self) -> bool:
        """Check if the pair is listed by Huobi."""

        url = f"{self.api}/v2/settings/common/symbols/"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                log.debug({"{self.exchange} _check_pair_exists response": resp})
                resp = await resp.json()
                for symbol in resp["data"]:
                    if symbol["sc"] == self.pair and symbol["state"] == "online":
                        log.info(
                            f'{self.exchange} pair "{self.pair}" is offered. MONITORING {self.exchange}'
                        )
                        return True

                log.warning(
                    f'{self.exchange} pair "{self.pair}" IS NOT offered. NOT MONITORING {self.exchange}.'
                )
                return False

    async def _subscribe(self, ws):
        await ws.send_str(json.dumps({"sub": f"market.{self.pair}.ticker"}))

        # huobi sometimes returns {'ping': 1654931160555} as first response, so we have to try and filter
        # example for fail {'status': 'error', 'ts': 1654930506284, 'err-code': 'bad-request', 'err-msg': 'invalid symbol btcusd'}
        # example for success {'id': None, 'status': 'ok', 'subbed': 'market.btcusdt.ticker', 'ts': 1654930486190}
        raw_resp = await ws.receive_bytes()
        resp = json.loads(gzip.decompress(raw_resp).decode())

        # if {'ping': <ts>} is the response, try again
        if "ping" in resp.keys():
            raw_resp = await ws.receive_bytes()
            resp = json.loads(gzip.decompress(raw_resp).decode())

        if resp["status"] == "ok":
            log.debug(f"{self.exchange} Subscribed to {self.pair}")
            return True

        log.warning(f"{self.exchange} Unable to Subscribe {resp}")
        return False

    async def run(self) -> None:
        """Fetch the price from Huobi."""

        # don't monitor the exchange if the pair isn't listed
        if not await self._check_pair_exists():
            return

        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    ws = await session.ws_connect(self.api_ws)
                    log.debug(
                        f"{self.exchange} Created new Client session and Established a websocket connection towards {self.api_ws}"
                    )

                    if not await self._subscribe(ws):
                        return
                    while True:
                        # https://huobiapi.github.io/docs/spot/v1/en/#q4-why-the-websocket-is-often-disconnected
                        # Q4：Why the WebSocket is often disconnected?
                        # Please check below possible reasons:

                        # The client didn't respond 'Pong'. It is requird to respond 'Pong' after receive 'Ping' from server.
                        # The server didn't receive 'Pong' successfully due to network issue.
                        # The connection is broken due to network issue.
                        # It is suggested to implement WebSocket re-connect mechanism. If Ping/Pong works well but the connection is broken, the application should be able to re-connect automatically.

                        # The aiohttp ws connection should send a pong response to each received ping, yet we get disconnected every 5 seconds or so, so we restart the connection

                        # example responses:
                        # {'ch': 'market.btcusdt.ticker', 'ts': 1654932129289, 'tick': {'open': 30082.59, 'high': 30186.19, 'low': 28841.12, 'close': 29342.99, 'amount': 16438.237897971736, 'vol': 483399849.8806693, 'count': 521649, 'bid': 29342.98, 'bidSize': 6.133091, 'ask': 29342.99, 'askSize': 2.129672, 'lastPrice': 29342.99, 'lastSize': 0.00737}}
                        # {'ping': 1654932128921}
                        try:
                            raw_resp = await ws.receive_bytes()
                            resp = json.loads(gzip.decompress(raw_resp).decode())
                            log.debug(f"{self.exchange} {resp}")

                            if "tick" in resp:
                                self.data = {
                                    "price": float(resp["tick"]["lastPrice"]),
                                    "time": datetime.utcfromtimestamp(
                                        resp["ts"] / 1000
                                    ).strftime("%Y/%m/%dT%H:%M:%S.%f"),
                                }
                        # Huobi disconnects & reconnects every few seconds, so we dont flood the log
                        except (asyncio.exceptions.TimeoutError) as e:
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
