import asyncio
import sys
import os
import logging
import dotenv
from datetime import datetime
from typing import Any

# custom
from utils.parser import parse_args
from exchanges.base import BaseExchange
from exchanges.binance import Binance
from exchanges.ftx import FTX
from exchanges.bybit import ByBit
from exchanges.huobi import Huobi
from exchanges.kucoin import KuCoin

from platforms.base import BasePlatform
from platforms.twitter import Twitter

from calculateandnotify import CalculateAndNotify


async def main() -> None:
    """Initialize each exchange's infinite loop."""

    # initialize each exchange's class
    exchanges: dict[str, BaseExchange] = {
        "binance": Binance(pair["merged"]),
        "ftx": FTX(pair["/"]),
        "bybit": ByBit(pair["merged"]),
        "huobi": Huobi(pair["merged"]),
        "kucoin": KuCoin(pair["-"]),
    }

    # initialize each platform's class
    platforms: dict[str, BasePlatform] = {
        "twitter": Twitter(args.cooldown),
    }

    calculate_and_notify = CalculateAndNotify(
        pair=pair, exchanges=exchanges, platforms=platforms, threshold=args.threshold
    )

    await asyncio.gather(
        exchanges["binance"].run(),
        exchanges["ftx"].run(),
        exchanges["bybit"].run(),
        exchanges["huobi"].run(),
        exchanges["kucoin"].run(),
        calculate_and_notify.run(),
    )


if __name__ == "__main__":
    """
    The whole program is assembled and ran here.
    """

    PROGRAM_DIR = os.path.dirname(os.path.realpath(__file__)) + "/../"

    # load the configuration file
    dotenv.load_dotenv(PROGRAM_DIR + ".env")

    # parse & validate the arguments
    args = parse_args()

    # Different exchanges use different notations, for example
    # FTX uses ETH/USDT while Binance uses ETHUSDT
    pair = {
        "base": args.base.lower(),
        "quote": args.quote.lower(),
        "-": f"{args.base}-{args.quote}",
        "/": f"{args.base}/{args.quote}",
        "merged": f"{args.base}{args.quote}",
    }

    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y/%m/%dT%H:%M:%S",
        handlers=[
            logging.FileHandler(f"{args.log_file}"),
            logging.StreamHandler(),
        ],
    )

    logging.info(f'STARTING. CMD: {" ".join(sys.argv)}')
    start = datetime.now()
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.exceptions.CancelledError) as e:
        logging.warning("Program Interrupted. Shutting down.")
    except BaseException as e:
        logging.exception(e)
    finally:
        end = datetime.now()
        ran = {}
        ran["days"] = (end - start).days
        ran["hours"], rem = divmod((end - start).seconds, 3600)
        ran["minutes"], ran["seconds"] = divmod(rem, 60)
        logging.info(
            f"PROGRAM RAN FOR {ran['days']} days {ran['hours']} hours {ran['minutes']} minutes and {ran['seconds']} seconds"
        )
