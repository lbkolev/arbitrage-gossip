import signal
import logging

logging.getLogger()


class Signal:
    """Signal handling for the program."""

    def __init__(self):
        ...

    def _sigterm_handler(self, signum: str, handler) -> None:
        """Signal handler for the program."""
        logging.warning("Received SIGTERM. EXITING.")
        raise KeyboardInterrupt

    def handle_signals(self) -> None:
        signal.signal(signal.SIGTERM, self._sigterm_handler)

        return None
