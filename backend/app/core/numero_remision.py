"""Número de remisión: un mismo número puede estar escrito con o sin ceros
a la izquierda ("GTS-6528" = "GTS-006528"). En la base conviven los dos
(el histórico importado sin ceros, la numeración automática con 6 dígitos)
y NO se cambia lo guardado; aquí está la regla para compararlos y
mostrarlos.

- Pantalla y mensajes: sin ceros ("GTS-6528"), como formatNumeroRemision
  del frontend.
- Reportes Excel: prefijo + 6 dígitos ("GTS-006528"), la forma de las hojas
  de referencia del cliente (data_import/formatos/).
- Duplicados / importador: mismo prefijo y mismo consecutivo numérico.
Los números manuales que no siguen el patrón PREFIJO-DÍGITOS se dejan tal
cual en todo.
"""

import re

from sqlalchemy import func

from app.models.remision import Remision

_PATRON = re.compile(r"^([A-Za-z]+)-?0*(\d+)$")


def clave(numero: str | None) -> tuple[str, int] | None:
    """(PREFIJO, consecutivo) o None si no sigue el patrón."""
    m = _PATRON.match((numero or "").strip())
    return (m.group(1).upper(), int(m.group(2))) if m else None


def para_mostrar(numero: str | None) -> str:
    c = clave(numero)
    return f"{c[0]}-{c[1]}" if c else (numero or "")


def para_reporte(numero: str | None) -> str:
    c = clave(numero)
    return f"{c[0]}-{c[1]:06d}" if c else (numero or "")


def condicion_mismo_numero(numero: str):
    """WHERE que encuentra la remisión con ese número escrito de cualquiera
    de las dos formas (con o sin ceros, mayúsculas o no)."""
    c = clave(numero)
    if c is None:
        return Remision.numero_remision == numero.strip()
    return func.upper(Remision.numero_remision).op("~")(f"^{c[0]}-?0*{c[1]}$")
