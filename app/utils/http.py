import asyncio
import logging
from typing import Optional, Literal, NamedTuple
from types import MappingProxyType

from httpx import AsyncClient, Response, HTTPError
from httpx import ConnectError
from cachetools import TTLCache
from app.utils import parse_content_type

logger = logging.getLogger(__name__)
_CACHE = TTLCache(maxsize=1024, ttl=3600)


class InfoResponse(NamedTuple):
    response: Response
    exception: Exception


class UrlType(NamedTuple):
    url: str
    content_type: str
    status_code: int
    error: Exception


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
    async def get_type(cls, *urls: str, **kwargs):
        async with cls(**kwargs) as http:
            return await http.get_url_type(*urls)

    @classmethod
    async def get_response(cls, *urls: str, **kwargs):
        async with cls(**kwargs) as http:
            return await http.get_url_response(*urls)

    async def get_url_response(self, *urls: str):
        data = await self.__fetch(*urls)
        return MappingProxyType({url: i.response for url, i in data.items() if i.response})

    async def __fetch(self, *urls: str):
        urls = sorted(set(urls))
        responses = await asyncio.gather(*(self.__get(url, "GET") for url in urls))
        return MappingProxyType({url: response for url, response in zip(urls, responses)})

    async def get_url_type(self, *urls: str):
        content_types: dict[str, UrlType] = {}
        urls_to_fetch: list[str] = []

        for url in sorted(urls):
            cached = _CACHE.get(url)
            if isinstance(cached, UrlType):
                content_types[url] = cached
            else:
                urls_to_fetch.append(url)

        if urls_to_fetch:
            responses = await asyncio.gather(*(self.__get(url, "HEAD") for url in urls_to_fetch))
            for url, response in zip(urls_to_fetch, responses):
                val = self.__get_url_type(url, response)
                _CACHE[url] = val
                content_types[url] = val

        return MappingProxyType(content_types)

    async def aclose(self):
        if self.__client is not None and not self.__client.is_closed:
            await self.__client.aclose()

    def __get_url_type(self, url: str, r: InfoResponse):
        url_type = UrlType(
            url=url,
            content_type=None,
            status_code=None,
            error=r.exception
        )
        if r.response is None:
            return url_type
        url_type = url_type._replace(
            url=str(r.response.url),
            status_code=r.response.status_code,
            content_type=parse_content_type(r.response.headers.get('content-type'))
        )
        return url_type

    async def __get(self, url: str, method: Literal["GET", "HEAD"]):
        """Fetch URL with simple retry/backoff logic using httpx.AsyncClient.

        Raises the last exception if all retries fail.
        """
        if self.__client is None or self.__client.is_closed:
            self.__client = AsyncClient(
                timeout=self.__timeout,
                follow_redirects=True,
            )
        resp: Response | None = None
        last_exc: Optional[HTTPError | ConnectError] = None
        for attempt in range(1, self.__retries + 1):
            try:
                if method == "GET":
                    resp = await self.__client.get(url)
                elif method == "HEAD":
                    resp = await self.__client.head(url)
                else:
                    raise ValueError(method)

                resp.raise_for_status()
                return InfoResponse(
                    response=resp,
                    exception=None
                )
            except (HTTPError, ConnectError) as exc:
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
        return InfoResponse(
            response=resp,
            exception=last_exc
        )
