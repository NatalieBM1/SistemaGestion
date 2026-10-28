"""agregar_reset_password_token_a_usuarios

Revision ID: 89a56447c6d0
Revises: 213a424fce90
Create Date: 2026-10-27 22:33:47.932684

Agrega dos columnas a la tabla 'usuarios' para el flujo de recuperación
de contraseña por código de email:
  - reset_token: código numérico de 6 dígitos (almacenado como hash bcrypt)
  - reset_token_expires: timestamp UTC de expiración del código
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "89a56447c6d0"
down_revision: Union[str, Sequence[str], None] = "213a424fce90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("reset_token", sa.String(), nullable=True))
    op.add_column("usuarios", sa.Column("reset_token_expires", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("usuarios", "reset_token_expires")
    op.drop_column("usuarios", "reset_token")
