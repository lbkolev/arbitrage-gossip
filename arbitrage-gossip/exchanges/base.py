from abc import ABC, abstractmethod


class BaseExchange(ABC):
    """Abstract class representing mandatory methods.

    Abstract class representing all the methods that
    have to be implemented by each monitored exchange(subclass).
    """

    @abstractmethod
    def __init__(self) -> None:
        ...

    @abstractmethod
    async def check_pair_exists(self) -> bool:
        """Check if a pair exists for a given exchange."""
        ...

    @abstractmethod
    async def run(self) -> None:
        """Run an async infinite loop fetching the price."""
        ...
