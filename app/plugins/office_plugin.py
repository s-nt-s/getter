from typing import Any, Dict

from app.utils.http import Http, Response

from app.plugins.base import FetcherPlugin
from markitdown import MarkItDown
from io import BytesIO
from ..utils.md import MD


class OfficePlugin(FetcherPlugin):
    name = "office"
    content_type: tuple[str] = (
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        #'application/vnd.ms-powerpoint',
    )

    def __init__(self):
        super().__init__()
        self.__md = MarkItDown()

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
        with BytesIO(r.content) as f:
            md = self.__md.convert(f)
            text = md.text_content
            return {
                "url": str(r.url),
                "text": text.rstrip(),
                "links": MD.get_links(text)
            }
