import asyncio
import aiohttp
import json
import sys

async def _subscribe(ws) -> bool:
    await ws.send_str(json.dumps(
        {"event" : "subscribe",
        "channel" : 'ticker',
        'symbol' : sys.argv[1],
        }
        )
    )

    # first response is of the type
#{'event': 'info', 'version': 2, 'serverId': '10f0969e-4291-4afc-ad35-02c80d847e6f', 'platform ': {'status': 1}}
    # the second gives us indication if we are actually subscribed
#{'event': 'subscribed', 'channel': 'ticker', 'chanId': 627364, 'symbol': 'tBTCUST', 'pair': 'BTCUST'}
    await ws.receive_json()
    resp = await ws.receive_json()
    print(resp)
    if resp['event'] == 'subscribed':
        # log..
        return True

    # log..
    return False

async def bitfinex() -> None:
    async with aiohttp.ClientSession() as session:
        while True:
            ws = await session.ws_connect('wss://api-pub.bitfinex.com/ws/2')
            if not await _subscribe(ws):
                return
            while True:
                # example responses:
                # [318834, [29278, 12.84014315, 29283, 8.850295029999998, -795, -0.0264, 29283, 628.17665028, 30182, 28864]]
                # [318834, 'hb']
                try:
                    resp = await ws.receive_json()
                    print(resp)
                except BaseException as e:
                    print(str(e))
                    break


if __name__ == "__main__":
    asyncio.run(bitfinex())
