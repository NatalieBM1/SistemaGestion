"""solo GTM es prefijo manual

Revision ID: 213a424fce90
Revises: 549c342624e6
Create Date: 2026-10-24 19:49:09.773994

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '213a424fce90'
down_revision: Union[str, Sequence[str], None] = '549c342624e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Regla de negocio nueva: el único prefijo manual (consecutivo
    escrito a mano) es GTM. Antes de esta migración, GTM y MAN tenían
    es_manual=true; el resto ya estaba en false. Idempotente: se puede
    correr varias veces sin efecto adicional. Verificado antes de
    escribirla que ningún prefijo distinto de GTM/MAN tenía es_manual=true,
    y que MAN no tiene ninguna remisión asociada (0 filas), así que no
    rompe numeración existente."""
    op.execute("UPDATE prefijos SET es_manual = true WHERE codigo = 'GTM'")
    op.execute("UPDATE prefijos SET es_manual = false WHERE codigo <> 'GTM'")


def downgrade() -> None:
    """Revierte al estado conocido antes de esta migración (GTM y MAN
    manuales, el resto automático) — es el único estado histórico del que
    hay evidencia; no se puede reconstruir si hubiera habido otra
    combinación."""
    op.execute("UPDATE prefijos SET es_manual = true WHERE codigo IN ('GTM', 'MAN')")
    op.execute("UPDATE prefijos SET es_manual = false WHERE codigo NOT IN ('GTM', 'MAN')")
