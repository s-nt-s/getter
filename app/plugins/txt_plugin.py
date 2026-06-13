from typing import Any, Dict

from app.utils.http import Http, Response

from app.plugins.base import FetcherPlugin
from app.utils.model import TxtResult


class TxtPlugin(FetcherPlugin):
    name = "txt"
    content_type = (
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
            obj[url] = plg._parse(resp)
        return obj

    def _parse(self, r: Response) -> Dict[str, Any]:
        return TxtResult.build_from_response(
            r,
            text=r.text.rstrip()
        )
