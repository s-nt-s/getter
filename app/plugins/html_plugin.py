from ..utils.html import buildSoup, get_text, iter_href
from ..utils.md import MD
from ..utils import safe_get_parsed_url, get_parsed_url

from app.utils.http import Http, Response

from app.plugins.base import FetcherPlugin


class HtmlPlugin(FetcherPlugin):
    name = "html"
    content_type: tuple[str] = ('html', )

    @classmethod
    def is_for_me(cls, url: str, content_type: str):
        if content_type not in cls.content_type:
            return False
        return True

    @classmethod
    async def parse(cls, *urls: str):
        plg = cls()
        r = await Http.get_response(*urls)
        obj: dict[str, dict[str]] = {}
        for url, resp in r.items():
            try:
                obj[url] = plg._parse(resp)
            except Exception as e:
                obj[url] = e
        return obj

    def _parse(self, r: Response):
        text = r.text

        soup = buildSoup(str(r.url), text)
        arr: list[str] = [get_parsed_url(str(r.url))]
        for _, _, link in iter_href(soup):
            link = safe_get_parsed_url(link)
            if isinstance(link, str) and link not in arr:
                arr.append(link)

        return {
            "url": arr.pop(0),
            "title": get_text(soup.select_one("title")),
            "html": str(soup),
            "markdown": MD.convert(soup.select_one("body")),
            "links": tuple(arr)
        }
