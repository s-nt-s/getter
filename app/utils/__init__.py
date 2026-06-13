from urllib.parse import quote, unquote, parse_qs, urlsplit, urlunsplit
from urllib.parse import urljoin


def get_first(data: dict | None, *args):
    if data is not None:
        for k in args:
            v = data.get(k)
            if v is not None:
                return v
    return None


def safe_get_parsed_url(url: str):
    try:
        return get_parsed_url(url)
    except Exception as e:
        return e


def get_parsed_url(url: str):
    if url is None:
        return None
    url = url.strip()
    if len(url) == 0:
        return None

    parsed = urlsplit(url)

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    if scheme not in ("http", "https") or not netloc:
        return None

    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    elif scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]

    # Decodificar percent-encoding de caracteres no reservados y volver a codificar
    # Primero decodificamos todo para normalizar mayúsculas en %XX y luego
    # re-codificamos excepto los caracteres no reservados
    path = unquote(parsed.path, errors='strict')
    path = quote(path, safe="/:@!$&'()*+,;=") 

    # Eliminar segmentos "." y ".." (path absoluto)
    path = urljoin("http://x", path)  # Esto elimina ./ y ../
    # Luego quitamos la parte de "http://x" que queda al principio
    if path.startswith("http://x"):
        path = path[len("http://x"):]
    if not path.startswith("/"):
        path = "/" + path
    # Si la URL original no tenía path, dejarlo vacío en lugar de "/"
    if parsed.path == "" and not parsed.query:
        path = ""

    # Normalizar query string: ordenar parámetros alfabéticamente
    sorted_query = parsed.query or ""
    if sorted_query:
        params = parse_qs(sorted_query, keep_blank_values=True)
        # parse_qs devuelve dict con listas; convertimos a lista de tuplas (clave, valor)
        flat_params = [(k, v[0]) for k, v in sorted(params.items()) if v[0] !=  '']
        # Si el valor está vacío, lo ponemos sin '='
        sorted_query = "&".join(f"{k}={v}" if v else k for k, v in flat_params)

    # El fragmento no es relevante
    fragment = ""

    # Reconstruir
    normalized = urlunsplit((scheme, netloc, path, sorted_query, fragment))
    return normalized


def all_subclasses(cls):
    result = set()

    for subclass in cls.__subclasses__():
        result.add(subclass)
        result.update(all_subclasses(subclass))

    return tuple(result)


def parse_content_type(t: str | None):
    if not t:
        return None

    t = t.split(";", 1)[0].strip().lower()
    if len(t) == 0:
        return None

    return t
