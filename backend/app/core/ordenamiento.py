"""Ayudas para el orden de las listas paginadas en el servidor.

Cada router mantiene su propia lista blanca de columnas ordenables
(``COLUMNAS_ORDENABLES_*``): aquí solo se arma el ORDER BY.

- Siempre se agrega un desempate por ``id``: sin él, al ordenar por una
  columna con valores repetidos (fecha, estado, cliente…) Postgres puede
  devolver los empates en distinto orden en cada consulta y una fila
  aparecería en dos páginas o en ninguna.
- Los vacíos (NULL) van siempre al final, en ascendente y descendente.
- ``texto_como_numero``: para columnas de texto que guardan números (NIT,
  teléfono), así "98" va antes que "1085" y no al revés.
"""

from sqlalchemy import Numeric, case, cast, func

from app.core.texto import normalizar

_CON_TILDE = "ÁÉÍÓÚÜÑáéíóúüñ"
_SIN_TILDE = "AEIOUUNaeiouun"


def texto_como_numero(columna) -> list:
    """Solo-dígitos se comparan como número; el resto va después, por texto."""
    return [case((columna.op("~")(r"^\d+$"), cast(columna, Numeric)), else_=None), columna]


def texto_normalizado_sql(columna):
    """Columna en minúsculas y sin tildes, para comparar/ordenar igual que
    core.texto.normalizar (sin depender de la extensión unaccent)."""
    return func.lower(func.translate(columna, _CON_TILDE, _SIN_TILDE))


def orden_por_prioridad(columna, prioridad: list[str]) -> list:
    """Primero los valores de `prioridad`, en ese orden; después el resto
    alfabético. Sin distinguir mayúsculas ni tildes ("Metro cúbico" =
    "METRO CÚBICO")."""
    normal = texto_normalizado_sql(columna)
    posicion = case(
        {normalizar(v): i for i, v in enumerate(prioridad)}, value=normal, else_=len(prioridad)
    )
    return [posicion, normal]


def clausulas_orden(expresiones: list, sentido: str, desempate) -> list:
    desc = sentido == "desc"
    orden = [(e.desc() if desc else e.asc()).nulls_last() for e in expresiones]
    orden.append(desempate.desc() if desc else desempate.asc())
    return orden
