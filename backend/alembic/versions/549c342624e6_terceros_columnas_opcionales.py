"""terceros columnas opcionales

Revision ID: 549c342624e6
Revises: 4e926c71e865
Create Date: 2026-10-20 07:54:13.747549

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '549c342624e6'
down_revision: Union[str, Sequence[str], None] = '4e926c71e865'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Terceros: direccion, municipio_id, email, telefono y regimen pasan
    a ser opcionales (antes NOT NULL). Solo identificacion y nombre
    siguen obligatorios. Aditiva: no borra ni transforma ningún dato
    existente, solo quita la restricción NOT NULL."""
    op.alter_column("terceros", "direccion", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column("terceros", "municipio_id", existing_type=sa.INTEGER(), nullable=True)
    op.alter_column("terceros", "email", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column("terceros", "telefono", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column("terceros", "regimen", existing_type=sa.VARCHAR(), nullable=True)


def downgrade() -> None:
    """Revierte a NOT NULL. Si para entonces hay filas con NULL en estas
    columnas, esta migración de vuelta falla (a propósito: no se inventan
    valores de reemplazo)."""
    op.alter_column("terceros", "regimen", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("terceros", "telefono", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("terceros", "email", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("terceros", "municipio_id", existing_type=sa.INTEGER(), nullable=False)
    op.alter_column("terceros", "direccion", existing_type=sa.VARCHAR(), nullable=False)
