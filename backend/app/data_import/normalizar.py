"""Reglas de normalización de la carga histórica (Bloque 2).

Nada de aquí inventa valores: si algo no se puede interpretar devuelve None
y quien llama lo reporta.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation

_ESPACIOS = re.compile(r"\s+")


def sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def clave(valor) -> str:
    """Clave de comparación: mayúsculas, sin tildes, espacios simples."""
    if valor is None:
        return ""
    return _ESPACIOS.sub(" ", sin_tildes(str(valor)).upper()).strip()


def texto(valor) -> str | None:
    """Texto recortado; vacío → None. Números enteros sin ".0"."""
    if valor is None:
        return None
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    t = str(valor).strip()
    return t or None


def identificacion(valor) -> str | None:
    """Identificación como texto exacto (sin decimales ni espacios)."""
    return texto(valor)


def decimal(valor) -> Decimal | None:
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return None
    if isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        return Decimal(str(valor))
    try:
        return Decimal(str(valor).strip().replace(",", "."))
    except InvalidOperation:
        return None


def entero(valor) -> int | None:
    d = decimal(valor)
    if d is None or d != d.to_integral_value():
        return None
    return int(d)


def fecha(valor) -> date | None:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    return None


_HORA_TEXTO = re.compile(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$")


def hora(valor) -> tuple[time | None, bool]:
    """(hora HH:MM, interpretable). Vacío → (None, True).

    Acepta datetime.time, datetime (toma la hora), decimales de Excel
    (0,4375 = 10:30; si trae parte entera se usa solo la fracción) y textos
    "6:00" o "00:00:00"."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return None, True
    if isinstance(valor, datetime):
        return time(valor.hour, valor.minute), True
    if isinstance(valor, time):
        return time(valor.hour, valor.minute), True
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        fraccion = float(valor) % 1
        minutos = round(fraccion * 24 * 60)
        if minutos == 24 * 60:
            minutos = 0
        return time(minutos // 60, minutos % 60), True
    m = _HORA_TEXTO.match(str(valor).strip())
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        if h < 24 and mi < 60:
            return time(h, mi), True
    return None, False


_NUMERO = re.compile(r"^\s*([A-Za-z]+)\s*-?\s*0*(\d+)\s*$")


def numero_remision(valor) -> tuple[str, int] | None:
    """("GTS", 6525) para "GTS-6525" o "GTS-006525"."""
    m = _NUMERO.match(str(valor or ""))
    return (m.group(1).upper(), int(m.group(2))) if m else None


def numero_factura(valor) -> str | None:
    """"f-7-1780" → "F-7-1780"; recorta espacios. "L-201-455" queda igual."""
    t = texto(valor)
    return t.upper() if t else None


def serie_factura(numero: str) -> str:
    """"F-7-1780" → "F-7"; "F-1234" → "F"."""
    partes = numero.split("-")
    return "-".join(partes[:-1]) if len(partes) > 1 else numero


ESTADOS = {
    "FACTURADA": "FACTURADA",
    "FACTURADA PARCIALMENTE": "FACTURADA_PARCIAL",
    "FACTURADA PARCIAL": "FACTURADA_PARCIAL",
    "NO FACTURADA": "NO_FACTURADA",
    "NO APLICA FACTURACION": "NO_APLICA",
}


def estado(valor) -> str | None:
    return ESTADOS.get(clave(valor))


TIPOS_SERVICIO = {"DESALOJOS": "DESALOJO"}


def tipo_servicio(valor) -> str | None:
    t = texto(valor)
    if t is None:
        return None
    k = clave(t)
    return TIPOS_SERVICIO.get(k, k)


UNIDADES = {"UNIDADES": "UNIDAD", "METROS CUBICOS": "Metro cúbico", "METRO CUBICO": "Metro cúbico"}


def unidad(valor) -> str | None:
    """None para vacío o "0" (filas desplazadas: no se inventa la unidad)."""
    if valor in (None, 0, "0") or (isinstance(valor, str) and not valor.strip()):
        return None
    k = clave(valor)
    return UNIDADES.get(k, k)


def nombre_catalogo(valor) -> str | None:
    """Nombre de catálogo en mayúsculas (la app guarda así los nombres)."""
    t = texto(valor)
    return _ESPACIOS.sub(" ", t).upper() if t else None
