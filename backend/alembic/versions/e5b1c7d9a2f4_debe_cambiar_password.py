"""cambio de contraseña obligatorio

Revision ID: e5b1c7d9a2f4
Revises: d7e4a1c9b2f3
Create Date: 2026-11-16 16:30:00.000000

Agrega usuarios.debe_cambiar_password (por defecto false). Mientras esté en
true, el usuario solo puede ver su sesión, cambiar su contraseña o cerrar
sesión. Se activa para el administrador inicial de producción, para los
usuarios creados en producción y cuando un administrador restablece una
contraseña. No cambia a ningún usuario existente.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5b1c7d9a2f4"
down_revision: Union[str, Sequence[str], None] = "d7e4a1c9b2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    columnas = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("usuarios")}
    if "debe_cambiar_password" not in columnas:
        op.add_column(
            "usuarios",
            sa.Column("debe_cambiar_password", sa.Boolean(), nullable=False, server_default=sa.false()),
        )


def downgrade() -> None:
    op.drop_column("usuarios", "debe_cambiar_password")
