"""Límite de intentos (rate limiting) para login y recuperación de contraseña.

Se limita por dos claves a la vez:

- **IP del cliente**: con el decorador ``@limiter.limit`` de slowapi.
- **Correo**: con ``limitar_por_correo`` dentro del endpoint, para que un
  atacante no pueda esquivar el límite rotando IPs sobre un mismo usuario.

La IP sale de ``request.client.host``. Detrás del proxy de Render ese valor
sería la IP del proxy (todos los usuarios compartirían una sola IP y se
bloquearían entre sí), por eso uvicorn se arranca con ``--proxy-headers
--forwarded-allow-ips='*'``: así uvicorn reemplaza ``client.host`` por la IP
real que viene en ``X-Forwarded-For``. Ver el comando exacto en el
Dockerfile y en NOTAS_RETOMAR.md.

Los contadores viven en memoria del proceso (``memory://``). Alcanza con un
solo proceso de uvicorn, que es como corre hoy en Render; si algún día se
usan varios workers o instancias, fijar RATE_LIMIT_STORAGE_URI a un Redis
(e instalar el paquete ``redis``) para que compartan los contadores.
"""

import math
import time

from fastapi import Request, status
from fastapi.responses import JSONResponse
from limits import RateLimitItem, parse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from app.core.config import settings

# Por IP es más holgado: una oficina con varios usuarios detrás de la misma
# IP pública comparte este cupo. El de correo es el que frena a quien prueba
# contraseñas contra una misma cuenta.
LIMITE_LOGIN_IP = "20/minute"
LIMITE_LOGIN_CORREO = "5/minute"
LIMITE_SOLICITAR_CODIGO = "3/hour"
# Usar el código para cambiar la contraseña (además del tope de 5 intentos
# fallidos por código, ver routers/auth.py).
LIMITE_USAR_CODIGO = "10 per 15 minutes"
ALCANCE_USAR_CODIGO = "codigo-recuperacion"


def ip_del_cliente(request: Request) -> str:
    return request.client.host if request.client else "desconocida"


limiter = Limiter(
    key_func=ip_del_cliente,
    storage_uri=settings.rate_limit_storage_uri,
    enabled=settings.rate_limit_enabled,
)


class LimiteExcedido(Exception):
    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after


def _segundos_para_reintentar(limite: RateLimitItem, *identificadores: str) -> int:
    reinicio, _restantes = limiter.limiter.get_window_stats(limite, *identificadores)
    return max(1, math.ceil(reinicio - time.time()))


def limitar_por_correo(regla: str, alcance: str, email: str) -> None:
    """Cuenta un intento para ``email`` en ``alcance``; lanza LimiteExcedido
    si ya se pasó de ``regla``. El correo se normaliza (minúsculas, sin
    espacios) para que "Ana@x.com" y "ana@x.com " cuenten juntos."""
    if not limiter.enabled:
        return
    limite = parse(regla)
    identificadores = ("correo", alcance, email.strip().lower())
    if not limiter.limiter.hit(limite, *identificadores):
        raise LimiteExcedido(_segundos_para_reintentar(limite, *identificadores))


def _describir_espera(segundos: int) -> str:
    if segundos < 60:
        return f"{segundos} segundo{'s' if segundos != 1 else ''}"
    minutos = math.ceil(segundos / 60)
    return f"{minutos} minuto{'s' if minutos != 1 else ''}"


def _respuesta_429(retry_after: int) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": (
                "Demasiados intentos. Por seguridad, espera "
                f"{_describir_espera(retry_after)} antes de volver a intentarlo."
            )
        },
        headers={"Retry-After": str(retry_after)},
    )


def manejar_rate_limit_excedido(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    # slowapi deja en request.state el límite que se excedió y su clave.
    limite_y_claves = getattr(request.state, "view_rate_limit", None)
    if limite_y_claves is None:
        return _respuesta_429(60)
    limite, claves = limite_y_claves
    return _respuesta_429(_segundos_para_reintentar(limite, *claves))


def manejar_limite_excedido(request: Request, exc: LimiteExcedido) -> JSONResponse:
    return _respuesta_429(exc.retry_after)
