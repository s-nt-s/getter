from ..utils.pdf import read_pdf
from typing import Any, Dict

from app.utils.http import Http, Response

from app.plugins.base import FetcherPlugin
from utils.model import TxtResult


class PdfPlugin(FetcherPlugin):
    name = "pdf"
    content_type: tuple[str] = ('pdf', )

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
        text = read_pdf(r)

        return TxtResult.build_from_response(r)._replace(
            text=text,
        )
