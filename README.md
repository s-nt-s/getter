Getter Service
==============

Servicio web extensible que recibe una URL, la visita usando el plugin adecuado y devuelve su contenido parseado como JSON.

Instalación
----------

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Ejecutar
------

```bash
uvicorn app.main:app --reload
```

API
---

POST /parse
Body: { "url": "https://..." }

Plugins
-------

- Los plugins se detectan automáticamente si están en `app/plugins/`.
- Un plugin debe heredar de `FetcherPlugin` y definir `pattern` y `async def parse(self, url)`.

Docker
------

Construir la imagen Docker:

```bash
docker build -t getter:latest .
```

Ejecutar la imagen en un contenedor:

```bash
docker run --rm -p 8000:8000 getter:latest
```

Crear servicio:

- Hacer ejecutable:

```bash
docker build -t getter:latest .
sudo cp getter.service /etc/systemd/system/getter.service
sudo systemctl daemon-reload
sudo systemctl enable --now getter.service
```

Prueba rápida (GET):

```bash
curl "http://127.0.0.1:8000/get?url=https://detectportal.firefox.com/success.txt"
```
