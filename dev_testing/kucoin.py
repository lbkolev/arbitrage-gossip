import aiohttp
import asyncio
import json
import sys
import time

# https://docs.kucoin.com/#apply-connect-token
# 'make request as follows to obtain the server list and temporary public token'
async def _get_api_ws_and_token():
    """Get the websocket url and the ping interval."""
    url = f"https://api.kucoin.com/api/v1/bullet-public"
    async with aiohttp.ClientSession() as session:
        async with session.post(url) as resp:
            resp = await resp.json()
            
            if int(resp["code"]) == 200000:
                api_ws = resp["data"]["instanceServers"][0]["endpoint"]
                token = resp["data"]["token"]

                return f"{api_ws}?token={token}"
            return False

async def _subscribe(ws):
    await ws.send_str(
        json.dumps(
            {
                "id": time.time(),
                "type": "subscribe",
                "topic": f"/market/ticker:{sys.argv[1]}",
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
    print(resp)
    if resp['type'] == 'ack':
        return True
    return False

async def kucoin():
    async with aiohttp.ClientSession() as session:
        while True:
            api_ws = await _get_api_ws_and_token()
            ws = await session.ws_connect(api_ws)

            if not await _subscribe(ws):
                return
            while True:
                try:
                    msg = await ws.receive_json()
                    print(msg)
                except TypeError as e:
                    sys.stdout.write(str(e))
                    break

if __name__ == "__main__":
    asyncio.run(kucoin())