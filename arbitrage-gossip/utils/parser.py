import argparse
import sys
import os
import logging


def parse_args() -> argparse.Namespace:
    argsparse = argparse.ArgumentParser("Arbitrage Gossiper")
    argsparse.add_argument(
        "-b",
        "--base",
        type=str,
        help="Base asset. ETHUSDT, ETH is base asset",
        required=True,
    )
    argsparse.add_argument(
        "-q",
        "--quote",
        type=str,
        help="Quote asset. ETHUSDT, USDT is quote asset",
        required=True,
    )
    argsparse.add_argument(
        "-t",
        "--threshold",
        type=float,
        help="The threshold specifies the discrepancy in percentage, after which the information will be reported to --report-to platforms. Defaults to 1 percent.",
        default=1,
    )
    argsparse.add_argument(
        "--log-level",
        type=str,
        help="Logging level. Defaults to info",
        default="info",
        choices=["debug", "info", "warning", "error"],
    )
    argsparse.add_argument(
        "--log-file",
        type=str,
        help="Specify a filename to log into. Defaults to {pair}.log. Log directory is by default /var/log/arbitrage-gossip",
        default="",
    )
    argsparse.add_argument(
        "--report-to",
        type=str,
        help="Comma separated list of the platforms we'll notify. **For now only twitter is supported**.",
        default="none",
    )
    argsparse.add_argument(
        "--cooldown",
        type=float,
        help="Report to the platforms every cooldown seconds. Defaults to 60 seconds",
        default=60.0,
    )
    args = argsparse.parse_args()

    # Verify the platforms we report to, currently only twitter is supported
    if args.report_to == "none":
        ...
    else:
        args.report_to = args.report_to.split(",")

        supported_platforms = ["twitter"]
        for platform in args.report_to:
            if platform not in supported_platforms:
                sys.stderr.write(f"Invalid --report-to platform: '{platform}'\n")
                argsparse.print_help()
                sys.exit(1)

    # Initialize the Logging level.
    if args.log_level.lower() == "debug":
        args.log_level = logging.DEBUG
    elif args.log_level.lower() == "info":
        args.log_level = logging.INFO
    elif args.log_level.lower() == "warning":
        args.log_level = logging.WARNING
    elif args.log_level.lower() == "error":
        args.log_level = logging.ERROR

    # Initialize the log file
    if not args.log_file:
        args.log_file = os.path.join('/var/log/arbitrage-gossip', f"{args.base.lower()}{args.quote.lower()}.log")
    return args
