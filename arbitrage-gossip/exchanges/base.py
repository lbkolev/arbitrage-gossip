from abc import ABC, abstractmethod
from typing import Any


class BaseExchange(ABC):
    """Abstract class representing mandatory methods.

    Abstract class representing all the methods that
    have to be implemented by each monitored exchange(subclass).
    """

    def __init__(
        self, pair: str, timeout: float = 10.0, receive_timeout: float = 60.0
    ) -> None:
        """Monitored pair"""
        self.pair = pair

        """ Exchange name """
        self.exchange = self.__class__.__name__

        """ Websocket connection timeout in seconds """
        self.timeout = timeout
        self.receive_timeout = receive_timeout

        """ Holds the latest price and timestamp fetched from the websocket
        self.data = {
            "price" : price,
            "time" : timestamp
            }
        """
        self.data: dict[str, Any] = {}

    @abstractmethod
    async def check_pair_exists(self) -> bool:
        """Check if a pair is listed by the exchange."""
        ...

    @abstractmethod
    async def run(self) -> None:
        """Run an infinite socket connection with the exchange, given that the pair is listed."""
        ...
