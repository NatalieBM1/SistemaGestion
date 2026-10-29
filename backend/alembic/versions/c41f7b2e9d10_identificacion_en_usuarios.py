"""identificacion en usuarios

Revision ID: c41f7b2e9d10
Revises: a3c9e1f04b72
Create Date: 2026-10-28 10:00:00.000000

Agrega a 'usuarios' la columna opcional 'identificacion' (cédula del
usuario, texto de hasta 30 caracteres). Sale en los reportes como "ID del
usuario" / "ID usuario" / "ID usuario factura". Queda vacía (NULL) para los
usuarios existentes: no se rellena ni se inventa ningún valor, y no se toca
ninguna remisión. Idempotente: si la columna ya existe no hace nada.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c41f7b2e9d10"
down_revision: Union[str, Sequence[str], None] = "a3c9e1f04b72"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existe() -> bool:
    columnas = sa.inspect(op.get_bind()).get_columns("usuarios")
    return any(c["name"] == "identificacion" for c in columnas)


def upgrade() -> None:
    if not _existe():
        op.add_column(
            "usuarios",
            sa.Column("identificacion", sa.String(length=30), nullable=True),
        )


def downgrade() -> None:
    if _existe():
        op.drop_column("usuarios", "identificacion")
