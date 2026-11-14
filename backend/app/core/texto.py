"""Comparación de textos de catálogo sin distinguir mayúsculas ni tildes.

Los catálogos se guardan en mayúsculas desde el cambio de normalización
("Cama baja" puede llegar a ser "CAMA BAJA"), así que las reglas que
dependen de un nombre no deben compararlo tal cual.
"""

import unicodedata


def normalizar(texto: str | None) -> str:
    texto = unicodedata.normalize("NFKD", (texto or "").strip().casefold())
    return "".join(c for c in texto if not unicodedata.combining(c))
