"""Registro de peticiones sin datos personales.

El log de accesos de uvicorn está desactivado (--no-access-log): imprime la
URL completa, con parámetros de búsqueda como ``?q=NOMBRE DEL CLIENTE``.
En su lugar, este middleware registra solo:

    GET /api/remisiones/{remision_id} 200 12ms

- método,
- la PLANTILLA de la ruta (no el valor real de los parámetros: ni ids, ni
  números de factura, ni textos de búsqueda; la query string nunca),
- código de estado y duración.
"""

import logging
import re
import time

logger = logging.getLogger("app.peticiones")

_SEGMENTO_VARIABLE = re.compile(r"/(\d+|[^/]*\d[^/]*)(?=/|$)")


def configurar_log_peticiones() -> None:
    """Salida a consola (Render guarda stdout) con un formato propio, sin
    depender de cómo configure uvicorn sus loggers."""
    if not logger.handlers:
        manejador = logging.StreamHandler()
        manejador.setFormatter(logging.Formatter("%(levelname)s:     %(message)s"))
        logger.addHandler(manejador)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def ruta_para_log(scope) -> str:
    """Plantilla de la ruta que atendió la petición; si no hubo ruta (404),
    el path con los segmentos que llevan dígitos reemplazados por {…}."""
    ruta = scope.get("route")
    plantilla = getattr(ruta, "path", None)
    if plantilla:
        return plantilla
    return _SEGMENTO_VARIABLE.sub("/{…}", scope.get("path", ""))


class RegistroPeticionesMiddleware:
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        inicio = time.perf_counter()
        estado = {"codigo": 500}

        async def send_con_estado(mensaje):
            if mensaje["type"] == "http.response.start":
                estado["codigo"] = mensaje["status"]
            await send(mensaje)

        try:
            await self.app(scope, receive, send_con_estado)
        finally:
            duracion_ms = (time.perf_counter() - inicio) * 1000
            logger.info(
                "%s %s %s %.0fms", scope["method"], ruta_para_log(scope), estado["codigo"], duracion_ms
            )
