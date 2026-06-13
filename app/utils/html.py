from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin
import logging
import re

logger = logging.getLogger(__name__)

re_sp = re.compile(r"\s+")
re_emb = re.compile(r"^image/[^;]+;base64,.*", re.I)


def iter_href(soup: BeautifulSoup):
    """Recorre los atributos href o src de los tags"""
    n: Tag
    for n in soup.select("img, form, a, iframe, frame, link, script, input"):
        attrs = {
            "a": "href",
            "link": "href",
            "form": "action"
        }.get(n.name, "src data-src").split()
        for attr in attrs:
            val = n.attrs.get(attr)
            if not isinstance(val, str) or len(val) == 0 or re_emb.search(val):
                continue
            if not val.startswith(("#", "javascript:")):
                yield n, attr, val


def buildSoup(root: str | None, source: str | None, parser="lxml"):
    if source is None:
        return None
    soup = BeautifulSoup(source, parser)
    if root:
        for n, attr, val in iter_href(soup):
            val = urljoin(root, val)
            n.attrs[attr] = val
    return soup


def get_text(n: Tag | None):
    if n is None:
        return None
    txt = n.get_text()
    txt = re_sp.sub(" ", txt).strip()
    if len(txt) == 0:
        return None
    return txt
