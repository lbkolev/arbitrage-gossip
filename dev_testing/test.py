import websockets
import asyncio
import aiohttp
import json
import sys

async def bitfinex(pair):
    async with websockets.connect("wss://api-pub.bitfinex.com/ws/2") as conn:
        await conn.send(json.dumps({
            "event" : 'subscribe',
            'channel' : 'ticker',
            'symbol' : pair,
            }))

        while True:
            s = await conn.recv()
            print(s)
            print('ftw')
            await asyncio.sleep(1)



async def subscribe(ws):
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
    if isinstance(resp, dict):
        if resp['event'] == 'subscribed':
            return True
        elif resp['event'] == 'error':
            # log..
            return False

    # log something else
    return False

async def bitfinex2(pair):
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('wss://api-pub.bitfinex.com/ws/2') as ws:
            if await subscribe(ws):
                while True:
                    resp = await ws.receive_json()
                    print(type(resp))
                    print(resp[1])

async def gemini():
    async with websockets.connect("wss://api.gemini.com/v1/marketdata/BTCUSDT"):
        ...

if __name__ == "__main__":
    asyncio.run(bitfinex2(sys.argv[1]))
