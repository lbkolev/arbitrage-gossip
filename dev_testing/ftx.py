import aiohttp
import asyncio
import json
import sys


async def _subscribe(ws) -> None:
    await ws.send_str(
        json.dumps(
            {
                "op": "subscribe",
                "channel": "ticker",
                "market": sys.argv[1],
            }
        )
    )

    # first response gives indication if we're subscribed
    # error looks like {'type': 'error', 'code': 404, 'msg': 'No such market: BTCUSDT'}
    # success looks like {'type': 'subscribed', 'channel': 'ticker', 'market': 'BTC/USDT'}
    resp = await ws.receive_json()
    if resp['type'] == 'subscribed':
        return True

    #log..
    return False


async def ftx() -> None:
    async with aiohttp.ClientSession() as session:
        while True:
            ws = await session.ws_connect("ws://ftx.com/ws")

            await _subscribe(ws)
            while True:
                try:
                    resp = await ws.receive_json()
                    print(resp)
                except BaseException as e:
                    print(str(e))
                    break

if __name__ == "__main__":
    asyncio.run(ftx())