
import pdftotext
from httpx import Response
from tempfile import NamedTemporaryFile
import re

re_sp = re.compile(r"\s+")


def read_pdf(file: str | Response, **kwargs):
    if isinstance(file, Response):
        pdf_bytes = file.content
        # Crear un archivo temporal y escribir los bytes
        with NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
            tmp.write(pdf_bytes)
            tmp.flush()
            return read_pdf(tmp.name)

    with open(file, 'rb') as fl:
        pages: list[str] = []
        for p in map(str.rstrip, (pdftotext.PDF(fl, **kwargs))):
            if len(p):
                pages.append(p)
        if len(pages) == 0:
            return ''
        all_text = "\n".join(pages)
        return all_text
