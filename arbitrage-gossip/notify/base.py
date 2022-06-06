import os
import dotenv
from abc import ABC, abstractmethod


class BaseNotify(ABC):
    """Abstract class representing mandatory methods.

    Abstract class representing all the methods that
    have to be implemented by each notified platform(subclass).
    """

    @abstractmethod
    def __init__(self) -> None:
        ...

    @abstractmethod
    async def notify(self) -> bool:
        """Notify the platform when discrepancy occurs."""
        ...
