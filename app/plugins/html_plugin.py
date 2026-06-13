from app.utils.html import buildSoup, get_text, iter_href
from app.utils.md import MD
from app.utils import safe_get_parsed_url, get_parsed_url
from app.utils.model import BaseResult

from app.utils.http import Http, Response

from app.plugins.base import FetcherPlugin
from typing import Optional


class HtmlResult(BaseResult):
    html: str
    title: Optional[str] = None
    markdown: Optional[str] = None


class HtmlPlugin(FetcherPlugin):
    name = "html"
    content_type = (
        'text/html',
    )

    @classmethod
    def is_for_me(cls, url: str, content_type: str):
        if content_type not in cls.content_type:
            return False
        return True

    @classmethod
    async def parse(cls, *urls: str):
        plg = cls()
        r = await Http.get_response(*urls)
        obj: dict[str, HtmlResult] = {}
        for url, resp in r.items():
            obj[url] = plg._parse(resp)
        return obj

    def _parse(self, r: Response):
        text = r.text

        soup = buildSoup(str(r.url), text)
        arr: list[str] = [get_parsed_url(str(r.url))]
        for _, _, link in iter_href(soup):
            link = safe_get_parsed_url(link)
            if isinstance(link, str) and link not in arr:
                arr.append(link)

        return HtmlResult.build_from_response(
            r,
            links=tuple(arr),
            title=get_text(soup.select_one("title")),
            html=str(soup),
            markdown=MD.convert(soup.select_one("body")),
        )
