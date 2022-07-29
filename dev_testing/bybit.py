import asyncio
import aiohttp
import json
import sys

async def _subscribe(ws) -> bool:
    await ws.send_str(json.dumps(
        {"event" : "sub",
        "topic" : "realtimes",
        "params" : {"binary" : "false"},
        'symbol' : sys.argv[1],
        }
        )
    )

    resp = await ws.receive_json()
    # bybit returns code only if there's a problem
    # for example 
    # {'code': '-100010', 'desc': 'Invalid Symbols!'}
    # {'code': '-10002', 'desc': 'Invalid event!'}
    # else it directly returns the data
    # {'symbol': 'BTCUSDT', 'symbolName': 'BTCUSDT', 'topic': 'realtimes', 'params': {'realtimeInterval': '24h', 'binary': 'false'}, 'data': [{'t': 1654927909198, 's': 'BTCUSDT', 'sn': 'BTCUSDT', 'c': '29298.76', 'h': '30234.91', 'l': '28855.01', 'o': '30169.02', 'v': '3915.612362', 'qv': '115172990.1827463', 'm': '-0.0288', 'e': 301}], 'f': True, 'sendTime': 1654927911193}

    if 'code' not in resp:
        return True
    else:
        #log..
        return False


async def bybit() -> None:
    async with aiohttp.ClientSession() as session:
        while True:
            ws = await session.ws_connect('wss://stream.bybit.com/spot/quote/ws/v1')
            if not await _subscribe(ws):
                return 
            while True:
                try:
                    resp = await ws.receive_json()
                    print(resp)
                except BaseException as e:
                    print(str(e))
                    break

if __name__ == "__main__":
    asyncio.run(bybit())