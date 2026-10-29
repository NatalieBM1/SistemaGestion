"""Criterio único de fechas/hora del sistema: UTC SIN zona horaria (naive).

Todas las columnas de fecha-hora en Postgres son ``timestamp without time
zone`` y lo ya guardado está en UTC, así que se guarda y se compara siempre
con ``ahora_utc()``. No mezclar con datetimes con zona (``aware``): comparar
uno naive con uno aware lanza TypeError.

Única excepción: el ``exp`` de los JWT (core/security.py), que nunca toca la
base: python-jose lo convierte a segundos epoch.
"""

from datetime import datetime, timezone


def ahora_utc() -> datetime:
    """Reemplazo de ``datetime.utcnow()`` (obsoleto desde Python 3.12),
    con el mismo resultado: hora UTC actual, sin tzinfo."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
