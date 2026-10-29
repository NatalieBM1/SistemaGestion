"""reset_intentos y token_version en usuarios

Revision ID: a3c9e1f04b72
Revises: 89a56447c6d0
Create Date: 2026-10-27 23:20:00.000000

Agrega a 'usuarios':
  - reset_intentos: intentos fallidos con el código de recuperación vigente
    (el código se bloquea al llegar a 5).
  - token_version: versión que viaja en cada JWT; subirla invalida todas
    las sesiones abiertas del usuario.

Ambas NOT NULL con valor por defecto 0, así que los usuarios existentes
quedan en 0 y sus tokens actuales (sin "ver", que cuenta como 0) siguen
valiendo. Idempotente: si la columna ya existe no hace nada.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a3c9e1f04b72"
down_revision: Union[str, Sequence[str], None] = "89a56447c6d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLUMNAS = ("reset_intentos", "token_version")


def _columnas_existentes() -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns("usuarios")}


def upgrade() -> None:
    existentes = _columnas_existentes()
    for nombre in COLUMNAS:
        if nombre not in existentes:
            op.add_column(
                "usuarios",
                sa.Column(nombre, sa.Integer(), nullable=False, server_default="0"),
            )


def downgrade() -> None:
    existentes = _columnas_existentes()
    for nombre in reversed(COLUMNAS):
        if nombre in existentes:
            op.drop_column("usuarios", nombre)
