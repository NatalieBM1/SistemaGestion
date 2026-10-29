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

from sqlalchemy import Numeric, case, cast


def texto_como_numero(columna) -> list:
    """Solo-dígitos se comparan como número; el resto va después, por texto."""
    return [case((columna.op("~")(r"^\d+$"), cast(columna, Numeric)), else_=None), columna]


def clausulas_orden(expresiones: list, sentido: str, desempate) -> list:
    desc = sentido == "desc"
    orden = [(e.desc() if desc else e.asc()).nulls_last() for e in expresiones]
    orden.append(desempate.desc() if desc else desempate.asc())
    return orden
