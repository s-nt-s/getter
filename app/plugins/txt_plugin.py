from typing import Any, Dict

from app.utils.http import Http, Response

from app.plugins.base import FetcherPlugin
from utils.model import TxtResult


class TxtPlugin(FetcherPlugin):
    name = "txt"
    content_type: tuple[str] = (
        'text/plain',
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
        obj: dict[str, dict[str]] = {}
        for url, resp in r.items():
            try:
                obj[url] = plg._parse(resp)
            except Exception as e:
                obj[url] = e
        return obj

    def _parse(self, r: Response) -> Dict[str, Any]:
        return TxtResult.build_from_response(r)._replace(
            text=r.text.rsplit()
        )
