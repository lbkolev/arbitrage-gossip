import logging
import aiohttp
import asyncio.exceptions
import json
import time
from datetime import datetime
from typing import Any

from exchanges.base import BaseExchange

class KuCoin(BaseExchange):
    """Implements monitoring for KuCoin """

    """ Kucoin http api url  """
    api: str = "https://api.kucoin.com"

    def __init__(self, 
        pair, 
        timeout = 10.0, 
        receive_timeout = 60.0 
    ) -> None:

        """ Monitored pair """
        self.pair = pair.upper()

        """ Exchange name """
        self.exchange = self.__class__.__name__

        """ Websocket timeout in seconds """
        self.timeout = timeout
        self.receive_timeout = receive_timeout

        """ Holds all live websocket data """
        self.data : dict[str, Any] = {}

        """ If the pair isn't offered by the exchange =False else =True """
        self.monitor: bool

        logging.info(f"{self.exchange} Initialized with {self.__dict__}")

    async def check_pair_exists(self) -> bool:
        url = f"{self.api}/api/v1/symbols"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                logging.debug({"{self.exchange} check_pair_exists response" : resp})
                resp = await resp.json()
                for pairs in resp['data']:
                    if pairs['symbol'] == self.pair and pairs['enableTrading'] == True:
                        logging.info(
                            f'{self.exchange} pair "{self.pair}" is offered. MONITORING {self.exchange}'
                        )
                        return True

                    if pairs['symbol'] == self.pair and pairs['enableTrading'] == False:
                        logging.warning(
                            f'{self.exchange} pair "{self.pair}" is currently disabled. NOT MONITORING {self.exchange}'
                        )
                        return False
                
                f'{self.exchange} pair "{self.pair}" is offered. MONITORING {self.exchange}'
                return False

    # https://docs.kucoin.com/#apply-connect-token
    # 'make request as follows to obtain the server list and temporary public token'
    async def get_api_ws_and_token(self):
        url = f"{self.api}/api/v1/bullet-public"
        async with aiohttp.ClientSession() as session:
            async with session.post(url) as resp:
                resp = await resp.json()

                if int(resp['code']) == 200000:
                    api_ws = resp['data']['instanceServers'][0]['endpoint']
                    token = resp['data']['token']
                    ping_interval = resp['data']['instanceServers'][0]['pingInterval']

                    logging.debug(f"{self.exchange} Kucoin ws url: {api_ws}?token={token}")

                    return f"{api_ws}?token={token}", ping_interval

                logging.warning(f"{self.exchange} Unable to get ws url and token. NOT MONITORING {self.exchange}")
                return False

    async def run(self) -> None:
        """ Run an infinite socket connection if the pair is offered by the exchange """

        # don't monitor the exchange if the pair isn't listed
        if not self.monitor:
            return

        while True:
            api_ws, ping_interval = await self.get_api_ws_and_token()

            async with aiohttp.ClientSession() as session:
                logging.info(f"{self.exchange} Created new client session.")

                try:
                    ws = await session.ws_connect(
                        api_ws,
                        timeout=self.receive_timeout,
                        receive_timeout=self.receive_timeout,
                        heartbeat = ping_interval,
                    )
                    logging.info(
                        f"{self.exchange} Established a websocket connection towards {api_ws}"
                    )
                    
                    await ws.send_str(
                        json.dumps(
                            {
                                "id" : time.time(),
                                "type" : "subscribe",
                                "topic" : f"/market/ticker:{self.pair}",
                                "privateChannel" : False,
                                "response" : True
                            }
                        )
                    )
                    while True:
                        try:
                            msg = await ws.receive_json()
                            logging.debug(f"{self.exchange} {msg}")
                            if "data" in msg:
                                self.data = {
                                    "price" : float(msg['data']['price']),
                                    "time" : datetime.utcfromtimestamp(
                                        msg['data']['time'] / 1000
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

if __name__ == "__main__":

    async def main():
        import asyncio
        kucoin = KuCoin('ETH-USDT', 60, 60)

        kucoin.monitor = await kucoin.check_pair_exists()
        await kucoin.run()

    asyncio.run(main())


