from cachetools import TTLCache
from fastapi import FastAPI, HTTPException, Query, Body
from .utils import safe_get_parsed_url, get_first
from app.utils.http import Http, UrlType
from collections import defaultdict
from .plugins.base import FetcherPlugin
from typing import Type
from .utils.model import UrlsPayload, TxtResult, BaseModel

import logging

from app.plugins.registry import PluginRegistry

logger = logging.getLogger(__name__)

app = FastAPI(title="Getter Service", version="1.0")


registry = PluginRegistry()
_CACHE = TTLCache(maxsize=1024, ttl=3600)


def get_links(data: dict | None):
    if data is None:
        return None
    lks = data.get('links')
    if not isinstance(lks, tuple):
        return None
    if len(lks) > 0 and not all(isinstance(lk, str) for lk in lks):
        return None
    del data['links']
    if len(lks) == 0:
        return None
    return lks


@app.get("/get", response_model=dict[str, BaseModel], response_model_exclude_none=True)
@app.post("/get", response_model=dict[str, BaseModel], response_model_exclude_none=True)
async def parse_url_get(
    url: list[str] | None = Query(None),
    payload: UrlsPayload | None = Body(None),
) -> dict[str, BaseModel]:
    return await _parse_url_get(url, payload)


@app.get("/txt", response_model=dict[str, TxtResult], response_model_exclude_none=True)
@app.post("/txt", response_model=dict[str, TxtResult], response_model_exclude_none=True)
async def get_txt(
    url: list[str] | None = Query(None),
    payload: UrlsPayload | None = Body(None),
) -> dict[str, TxtResult]:
    obj: dict[str, TxtResult] = {}
    data = await _parse_url_get(url, payload)
    for url, page in data.items():
        p = page.model_dump()
        del p['data']
        p['text'] = get_first(page.data, 'markdown', 'text')
        obj[url] = TxtResult(**p)
    return obj


async def _parse_url_get(
    url: list[str] | None = Query(None),
    payload: UrlsPayload | None = Body(None),
) -> dict[str, BaseModel]:
    """Accept one or more URL query parameters or POST JSON payload and parse each with the plugin system."""
    urls = list(url or [])
    if payload is not None:
        urls.extend(payload.url)
    if not urls:
        raise HTTPException(status_code=400, detail="No URLs provided")
    obj: dict[str, BaseModel] = {}
    normalized_urls: dict[str, str] = {}

    for u in map(str, url):
        if u in normalized_urls:
            continue
        n = safe_get_parsed_url(u)
        if not isinstance(n, str):
            obj[u] = BaseModel(
                plugin=None,
                url=None,
                content_type=None,
                error=f"Malformed URL {n or ''}".strip()
            )
            continue
        normalized_urls[u] = n

    u_types = await Http.get_type(*normalized_urls.values())
    p_urls: dict[Type[FetcherPlugin], set[UrlType]] = defaultdict(set)
    for u, n in normalized_urls.items():
        t = u_types[n]
        r = _CACHE.get(t)
        if isinstance(r, BaseModel):
            obj[u] = r
            continue
        fr = BaseModel(
            plugin=None,
            url=t.url,
            content_type=t.content_type,
            status_code=t.status_code,
            error=str(t.error) if t.error else None
        )
        if isinstance(t.error, Exception):
            obj[u] = fr
            continue
        if t.content_type not in registry.content_type:
            obj[u] = fr._replace(
                error=f"content_type is not a supported one: {', '.join(registry.content_type)}"
            )
            continue
        try:
            plugin_cls = registry.find(t.url, t.content_type)
            p_urls[plugin_cls].add(t)
        except LookupError:
            obj[u] = fr._replace(
                error=f"content_type is not a supported one: {', '.join(registry.content_type)}"
            )
            continue

    tp_obj: dict[UrlType, BaseModel] = {}
    for plg, urls in p_urls.items():
        u_t = {t.url: t for t in urls}
        data = await plg.parse(*u_t.keys())
        for u, r in data.items():
            pr = BaseModel(
                plugin=plg.name,
                url=u,
                content_type=u_t[u].content_type,
                status_code=u_t[u].status_code,
            )
            if isinstance(r, Exception):
                tp_obj[u] = pr._replace(
                    error=str(r)
                )
            else:
                lks = get_links(r)
                tp_obj[u] = pr._replace(
                    data=r,
                    links=lks
                )

    for u, n in normalized_urls.items():
        t = u_types[n]
        r = tp_obj.get(t.url)
        if r is not None:
            obj[u] = r

    return obj
