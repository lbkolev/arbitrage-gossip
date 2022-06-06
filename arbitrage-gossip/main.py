#!/usr/bin/python

import asyncio
import sys, os
import logging
import dotenv
from datetime import datetime
from typing import Any

# custom
from utils.signal import Signal
from utils.parser import parse_args
from exchanges.binance import Binance
from exchanges.ftx import FTX
from exchanges.bybit import ByBit
from exchanges.huobi import Huobi
import prices


async def main() -> None:
    """Initialize each exchange's infinite loop."""

    # initialize each exchange's class
    exchanges: dict[str, Any] = {
        "binance": Binance(pair["merged"]),
        "ftx": FTX(pair["/"]),
        "bybit": ByBit(pair["merged"]),
        "huobi": Huobi(pair["merged"]),
    }

    # Check if the pair is offered by the exchange
    # if it isn't, run() will return right after getting called from asyncio.gather()
    exchanges["binance"].monitor = await exchanges["binance"].check_pair_exists()
    exchanges["ftx"].monitor = await exchanges["ftx"].check_pair_exists()
    exchanges["bybit"].monitor = await exchanges["bybit"].check_pair_exists()
    exchanges["huobi"].monitor = await exchanges["huobi"].check_pair_exists()

    await asyncio.gather(
        exchanges["binance"].run(),
        exchanges["ftx"].run(),
        exchanges["bybit"].run(),
        exchanges["huobi"].run(),
        prices.run(exchanges, pair, args.threshold, args.report_to, args.cooldown),
    )


if __name__ == "__main__":
    """
    The whole program is assembled and ran here.
    """

    PROGRAM_DIR = os.path.dirname(os.path.realpath(__file__)) + "/../"

    # load the configuration file
    dotenv.load_dotenv(PROGRAM_DIR + ".env")

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

    # Initialize Signal Handling.
    signal = Signal()
    signal.handle_signals()

    # Initialize the Logging level.
    if args.log_level.lower() == "debug":
        level = logging.DEBUG
    elif args.log_level.lower() == "info":
        level = logging.INFO
    elif args.log_level.lower() == "warning":
        level = logging.WARNING
    elif args.log_level.lower() == "error":
        level = logging.ERROR

    if not args.log_file:
        args.log_file = f"{pair['merged'].lower()}.log"

    if not os.path.exists(args.log_dir):
        try:
            os.mkdir(args.log_dir)
        except BaseException as e:
            print(e)
            sys.exit(1)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y/%m/%dT%H:%M:%S",
        handlers=[
            logging.FileHandler(f"{args.log_dir}/{args.log_file}"),
            logging.StreamHandler(),
        ],
    )

    logging.info(f'STARTING. CMD: {" ".join(sys.argv)}')
    time_start = datetime.now()
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.exceptions.CancelledError) as e:
        logging.warning("Program Interrupted.. Shutting down.")
    except BaseException as e:
        logging.exception(e)
    finally:
        time_end: datetime = datetime.now()

        time_ran: dict = {}
        time_ran["days"] = (time_end - time_start).days
        time_ran["hours"], rem = divmod((time_end - time_start).seconds, 3600)
        time_ran["minutes"], time_ran["seconds"] = divmod(rem, 60)

        logging.info(
            f"PROGRAM RAN FOR {time_ran['days']} days {time_ran['hours']} hours {time_ran['minutes']} minutes and {time_ran['seconds']} seconds"
        )
