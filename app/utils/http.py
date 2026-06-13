import asyncio
import logging
from typing import Optional, Literal, NamedTuple
from types import MappingProxyType

from httpx import AsyncClient, Response, HTTPError
from cachetools import TTLCache

logger = logging.getLogger(__name__)
_CACHE = TTLCache(maxsize=1024, ttl=3600)


class UrlType(NamedTuple):
    url: str
    content_type: str


class Http:
    def __init__(self, retries: int = 3, backoff: float = 0.5, timeout: float = 15.0):
        self.__retries = retries
        self.__backoff = backoff
        self.__timeout = timeout
        self.__client: Optional[AsyncClient] = None

    async def __aenter__(self):
        if self.__client is None or self.__client.is_closed:
            self.__client = AsyncClient(
                timeout=self.__timeout,
                follow_redirects=True,
            )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.aclose()

    @classmethod
    async def get_type(cls, *urls: Response | str, **kwargs):
        async with cls(**kwargs) as http:
            return await http.get_url_type(*urls)

    @classmethod
    async def get_response(cls, *urls: Response | str, **kwargs):
        async with cls(**kwargs) as http:
            return await http.fetch(*urls)

    async def fetch(self, *urls: str):
        urls = sorted(set(urls))
        responses = await asyncio.gather(*(self.__get(url, "GET") for url in urls))
        return MappingProxyType({url: response for url, response in zip(urls, responses)})

    async def get_url_type(self, *urls: Response | str):
        urls_to_inspect: set[str] = set()
        content_types: dict[str, UrlType] = {}
        urls_to_fetch: list[str] = []

        for item in urls:
            if isinstance(item, str):
                urls_to_inspect.add(item)
                continue
            content_types[str(item.url)] = self.__get_url_type(item)

        for url in sorted(urls_to_inspect.difference(content_types.keys())):
            cached = _CACHE.get(url)
            if isinstance(cached, UrlType):
                content_types[url] = cached
            else:
                urls_to_fetch.append(url)

        if urls_to_fetch:
            responses = await asyncio.gather(*(self.__get(url, "HEAD") for url in urls_to_fetch))
            for url, response in zip(urls_to_fetch, responses):
                val = self.__get_url_type(response)
                _CACHE[url] = val
                content_types[url] = val

        return MappingProxyType(content_types)

    async def aclose(self):
        if self.__client is not None and not self.__client.is_closed:
            await self.__client.aclose()

    def __get_url_type(self, r: Response):
        t = r.headers.get("content-type")
        url_type = UrlType(str(r.url), content_type=None)
        if not t:
            return url_type

        t = t.split(";", 1)[0].strip().lower()
        if not t:
            return url_type

        if t in ("application/pdf", "text/html"):
            t = t.split("/")[-1]

        return url_type._replace(content_type=t)

    async def __get(self, url: str, method: Literal["GET", "HEAD"]):
        """Fetch URL with simple retry/backoff logic using httpx.AsyncClient.

        Raises the last exception if all retries fail.
        """
        if self.__client is None or self.__client.is_closed:
            self.__client = AsyncClient(
                timeout=self.__timeout,
                follow_redirects=True,
            )

        last_exc: Optional[HTTPError] = None
        for attempt in range(1, self.__retries + 1):
            try:
                if method == "GET":
                    resp = await self.__client.get(url)
                elif method == "HEAD":
                    resp = await self.__client.head(url)
                else:
                    raise ValueError(method)

                resp.raise_for_status()
                return resp
            except HTTPError as exc:
                last_exc = exc
                wait = self.__backoff * (2 ** (attempt - 1))
                logger.debug(
                    "Attempt %d failed for %s: %s; retrying in %.2fs",
                    attempt,
                    url,
                    exc,
                    wait,
                )
                if attempt < self.__retries:
                    await asyncio.sleep(wait)

        logger.error(
            "All %d attempts failed for %s: %s",
            self.__retries,
            url,
            last_exc,
        )
        raise last_exc
