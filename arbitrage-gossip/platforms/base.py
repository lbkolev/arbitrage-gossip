import os
import dotenv
from abc import ABC, abstractmethod


class BasePlatform(ABC):
    """Abstract class representing mandatory methods.

    Abstract class representing all the methods that
    have to be implemented by each notified platform(subclass).
    """

    def __init__(self, cooldown: float) -> None:
        """The time of the last report"""
        self.last_reported: int = 0

        """Report to the platform every cooldown seconds"""
        self.cooldown = cooldown

        """ The platform's name """
        self.platform = self.__class__.__name__

    @abstractmethod
    async def notify(self) -> bool:
        """Notify the platform when discrepancy occurs."""
        ...
