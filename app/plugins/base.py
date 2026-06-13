from abc import ABC, abstractmethod
from ..utils.model import BaseResult
import logging

logger = logging.getLogger(__name__)


class FetcherPlugin(ABC):
    """Base class for URL fetch and parse plugins."""
    name: str = "base"
    content_type: tuple[str] = tuple()

    @classmethod
    @abstractmethod
    def is_for_me(cls, url: str, content_type: str) -> bool:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    async def parse(cls, *urls: str) -> dict[str, Exception | BaseResult]:
        raise NotImplementedError()

