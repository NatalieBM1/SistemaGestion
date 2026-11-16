"""carga histórica completa desde el Excel

Revision ID: d7e4a1c9b2f3
Revises: c41f7b2e9d10
Create Date: 2026-11-16 15:00:00.000000

Ajustes de esquema para cargar TODO el Excel histórico sin inventar valores:

- remisiones.estado_facturacion admite 'NO_APLICA' ("No aplica
  facturación"): no cuenta como pendiente ni se puede facturar.
- remisiones.ing_registro (fecha y hora "IngRegistro" del Excel, opcional).
- remision_productos.producto_id, .cantidad y .numero_viajes pasan a
  opcionales: hay filas del Excel sin producto, sin cantidad o sin número de
  viajes, y no se rellenan (antes el número de viajes vacío quedaba en 1).
- ordenes_servicio.valor_tope y .saldo_disponible pasan a opcionales: el
  Excel solo trae el número de la ODS. Sin tope no se controla saldo.
- activos.clase y .empresa_id pasan a opcionales: el Excel solo trae la placa.
- usuarios.email y .password_hash pasan a opcionales y se agrega
  usuarios.historico: los creadores históricos de remisiones quedan como
  usuarios inactivos, sin correo ni contraseña (no pueden iniciar sesión).
- terceros.ciudad: texto original de la columna CIUDAD de la hoja Terceros
  (además de municipio_id cuando se puede identificar el municipio).

Solo amplía lo permitido: no modifica ni borra datos existentes.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d7e4a1c9b2f3"
down_revision: Union[str, Sequence[str], None] = "c41f7b2e9d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ESTADOS_NUEVOS = "('NO_FACTURADA', 'FACTURADA_PARCIAL', 'FACTURADA', 'NO_APLICA')"
ESTADOS_ANTES = "('NO_FACTURADA', 'FACTURADA_PARCIAL', 'FACTURADA')"


def _columnas(tabla: str) -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(tabla)}


def upgrade() -> None:
    op.drop_constraint("ck_remisiones_estado_facturacion", "remisiones", type_="check")
    op.create_check_constraint(
        "ck_remisiones_estado_facturacion", "remisiones", f"estado_facturacion IN {ESTADOS_NUEVOS}"
    )
    if "ing_registro" not in _columnas("remisiones"):
        op.add_column("remisiones", sa.Column("ing_registro", sa.DateTime(), nullable=True))

    op.alter_column("remision_productos", "producto_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("remision_productos", "cantidad", existing_type=sa.Numeric(12, 3), nullable=True)
    op.alter_column("remision_productos", "numero_viajes", existing_type=sa.Integer(), nullable=True)

    op.alter_column("ordenes_servicio", "valor_tope", existing_type=sa.Numeric(14, 2), nullable=True)
    op.alter_column("ordenes_servicio", "saldo_disponible", existing_type=sa.Numeric(14, 2), nullable=True)

    op.alter_column("activos", "clase", existing_type=sa.String(), nullable=True)
    op.alter_column("activos", "empresa_id", existing_type=sa.Integer(), nullable=True)

    op.alter_column("usuarios", "email", existing_type=sa.String(), nullable=True)
    op.alter_column("usuarios", "password_hash", existing_type=sa.String(), nullable=True)
    if "historico" not in _columnas("usuarios"):
        op.add_column(
            "usuarios",
            sa.Column("historico", sa.Boolean(), nullable=False, server_default=sa.false()),
        )

    if "ciudad" not in _columnas("terceros"):
        op.add_column("terceros", sa.Column("ciudad", sa.String(), nullable=True))


def downgrade() -> None:
    # Solo es posible si no hay filas que usen lo que se habilitó arriba.
    op.drop_column("terceros", "ciudad")
    op.drop_column("usuarios", "historico")
    op.alter_column("usuarios", "password_hash", existing_type=sa.String(), nullable=False)
    op.alter_column("usuarios", "email", existing_type=sa.String(), nullable=False)
    op.alter_column("activos", "empresa_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("activos", "clase", existing_type=sa.String(), nullable=False)
    op.alter_column("ordenes_servicio", "saldo_disponible", existing_type=sa.Numeric(14, 2), nullable=False)
    op.alter_column("ordenes_servicio", "valor_tope", existing_type=sa.Numeric(14, 2), nullable=False)
    op.alter_column("remision_productos", "numero_viajes", existing_type=sa.Integer(), nullable=False)
    op.alter_column("remision_productos", "cantidad", existing_type=sa.Numeric(12, 3), nullable=False)
    op.alter_column("remision_productos", "producto_id", existing_type=sa.Integer(), nullable=False)
    op.drop_column("remisiones", "ing_registro")
    op.drop_constraint("ck_remisiones_estado_facturacion", "remisiones", type_="check")
    op.create_check_constraint(
        "ck_remisiones_estado_facturacion", "remisiones", f"estado_facturacion IN {ESTADOS_ANTES}"
    )
