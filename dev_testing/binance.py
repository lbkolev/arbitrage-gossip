import asyncio
import aiohttp
import sys

async def _subscribe() -> None:
    # binance doesn't work with subscription
    ...

async def binance() -> None:
    async with aiohttp.ClientSession() as session:
        while True:
            ws = await session.ws_connect(f"wss://stream.binance.com:9443/ws/{sys.argv[1]}@miniTicker")

            while True:
                try:
                    ss = await ws.receive()
                    print(ss)
                except BaseException as e:
                    sys.stdout.write(str(e))
                    break

if __name__ == "__main__":
    asyncio.run(binance())