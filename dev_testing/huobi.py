import aiohttp
import asyncio
import sys
import json
import gzip

async def subscribe(ws):
    await ws.send_str(json.dumps(
        {
            "sub": f"market.{sys.argv[1]}.ticker"
        }
        )
    )

    # huobi sometimes returns {'ping': 1654931160555} as first response, so we have to try and filter
    # example for fail {'status': 'error', 'ts': 1654930506284, 'err-code': 'bad-request', 'err-msg': 'invalid symbol btcusd'}
    # example for success {'id': None, 'status': 'ok', 'subbed': 'market.btcusdt.ticker', 'ts': 1654930486190}
    raw_resp = await ws.receive_bytes()
    resp = json.loads(gzip.decompress(raw_resp).decode())

    # if {'ping': <ts>} is the response, try again
    if 'ping' in resp.keys():
        raw_resp = await ws.receive_bytes()
        resp = json.loads(gzip.decompress(raw_resp).decode())

    if resp['status'] == 'ok':
        return True
    return False

async def huobi():
    async with aiohttp.ClientSession() as session:
        while True:
            ws = await session.ws_connect("wss://api-aws.huobi.pro/ws/v1",autoping=True)
            if not await subscribe(ws):
                return
            while True:
                # https://huobiapi.github.io/docs/spot/v1/en/#q4-why-the-websocket-is-often-disconnected
                # Q4：Why the WebSocket is often disconnected?
                #Please check below possible reasons:

                #The client didn't respond 'Pong'. It is requird to respond 'Pong' after receive 'Ping' from server.
                #The server didn't receive 'Pong' successfully due to network issue.
                #The connection is broken due to network issue.
                #It is suggested to implement WebSocket re-connect mechanism. If Ping/Pong works well but the connection is broken, the application should be able to re-connect automatically.
                
                # The aiohttp ws connection should send a pong response to each received ping, yet we get disconnected every 5 seconds or so, so we restart the connection
                try:
                    raw_resp = await ws.receive_bytes()
                    resp = json.loads(gzip.decompress(raw_resp).decode())

                    print(resp)
                except TypeError:
                    raw_resp = await ws.receive()
                    print(str(raw_resp))
                    #if raw_resp.type == aiohttp.WSMsgType.CLOSED:
                    #    break
                    break


if __name__ == "__main__":
    asyncio.run(huobi())
