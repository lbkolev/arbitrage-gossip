import argparse
import sys


def parse_args() -> argparse.Namespace:
    argsparse = argparse.ArgumentParser("Arbitrage Gossiper - v1.0 Alpha")
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
        "--log-dir",
        type=str,
        help="Log directory. Defaults to /var/log/arbitrager/",
        default="/var/log/arbitrager",
    )
    argsparse.add_argument(
        "--log-file",
        type=str,
        help="Specify a filename to log into. Defaults to {pair}.log",
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

    if args.report_to == "none":
        ...
    else:
        args.report_to = args.report_to.split(",")

        supported_platforms = ["twitter"]
        for platform in args.report_to:
            if platform not in supported_platforms:
                argsparse.print_help()
                sys.exit(1)

    return args
