"""Middlewares ASGI de seguridad HTTP.

- ``CabecerasSeguridadMiddleware``: agrega las cabeceras de seguridad a
  todas las respuestas de la API (HSTS solo en producción, porque en
  desarrollo se sirve por http://localhost).
- ``LimiteCuerpoMiddleware``: rechaza con 413 un multipart/form-data cuyo
  Content-Length ya declara más del máximo, ANTES de que Starlette lo lea y
  lo guarde. El límite exacto por archivo lo aplica después
  ``core/uploads.py`` leyendo por bloques.
"""

import json

from app.core.uploads import MAX_BYTES_EXCEL, MENSAJE_DEMASIADO_GRANDE

CABECERAS_BASE = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    (
        b"permissions-policy",
        b"camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    ),
    # Obsoleta y con efectos indeseados en navegadores viejos: se apaga.
    (b"x-xss-protection", b"0"),
]
HSTS = (b"strict-transport-security", b"max-age=31536000; includeSubDomains")

# Margen para los separadores y campos del multipart además del archivo.
MARGEN_MULTIPART = 64 * 1024


class CabecerasSeguridadMiddleware:
    def __init__(self, app, *, produccion: bool) -> None:
        self.app = app
        self.cabeceras = CABECERAS_BASE + ([HSTS] if produccion else [])

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def send_con_cabeceras(message):
            if message["type"] == "http.response.start":
                existentes = {k.lower() for k, _ in message.get("headers", [])}
                message.setdefault("headers", [])
                message["headers"] = list(message["headers"]) + [
                    (k, v) for k, v in self.cabeceras if k not in existentes
                ]
            await send(message)

        await self.app(scope, receive, send_con_cabeceras)


class LimiteCuerpoMiddleware:
    def __init__(self, app, *, max_bytes: int = MAX_BYTES_EXCEL + MARGEN_MULTIPART) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            cabeceras = dict(scope["headers"])
            tipo = cabeceras.get(b"content-type", b"")
            largo = cabeceras.get(b"content-length")
            if (
                tipo.startswith(b"multipart/form-data")
                and largo
                and largo.isdigit()
                and int(largo) > self.max_bytes
            ):
                cuerpo = json.dumps({"detail": MENSAJE_DEMASIADO_GRANDE}).encode()
                await send(
                    {
                        "type": "http.response.start",
                        "status": 413,
                        "headers": [
                            (b"content-type", b"application/json"),
                            (b"content-length", str(len(cuerpo)).encode()),
                            (b"connection", b"close"),
                        ],
                    }
                )
                await send({"type": "http.response.body", "body": cuerpo})
                return
        await self.app(scope, receive, send)
