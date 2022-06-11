from abc import ABC, abstractmethod
from typing import Any


class BaseExchange(ABC):
    """Abstract class representing mandatory methods.

    Abstract class representing all the methods - both public and private - that
    have to be implemented by each monitored exchange(subclass).
    """

    def __init__(self, pair: str) -> None:
        """Monitored pair"""
        self.pair = pair

        """ Exchange name """
        self.exchange = self.__class__.__name__

        """ Holds the latest price fetched from the websocket and date in the format %Y/%m/%dT%H:%M:%S.%f" 
        self.data = {
            "price" : price,
            "time"  : date
            }
        """
        self.data: dict[str, Any] = {}

    @abstractmethod
    async def _check_pair_exists(self) -> bool:
        """Check if a pair is listed by the exchange."""
        ...

    async def _subscribe(self) -> bool:
        """Subscribe to a given websocket channel."""
        ...

    @abstractmethod
    async def run(self) -> None:
        """Run an infinite socket connection with the exchange, given that the pair is listed."""
        ...
