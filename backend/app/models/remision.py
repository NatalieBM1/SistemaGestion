from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, Numeric, Text
from sqlmodel import Field, SQLModel

from app.core.fechas import ahora_utc


class Remision(SQLModel, table=True):
    __tablename__ = "remisiones"
    __table_args__ = (
        CheckConstraint(
            "estado_facturacion IN ('NO_FACTURADA', 'FACTURADA_PARCIAL', 'FACTURADA', 'NO_APLICA')",
            name="ck_remisiones_estado_facturacion",
        ),
        Index("ix_remisiones_fecha", "fecha"),
        Index("ix_remisiones_cliente_id", "cliente_id"),
        Index("ix_remisiones_estado_facturacion", "estado_facturacion"),
    )

    id: int | None = Field(default=None, primary_key=True)
    numero_remision: str = Field(unique=True)
    prefijo_id: int = Field(foreign_key="prefijos.id")
    consecutivo: str
    orden_servicio_id: int | None = Field(
        default=None, foreign_key="ordenes_servicio.id"
    )
    fecha: date
    forma_pago_id: int | None = Field(default=None, foreign_key="formas_pago.id")
    cliente_id: int = Field(foreign_key="terceros.id")
    conductor_id: int | None = Field(default=None, foreign_key="terceros.id")
    origen_municipio_id: int = Field(foreign_key="municipios.id")
    destino_municipio_id: int = Field(foreign_key="municipios.id")
    proyecto_id: int | None = Field(default=None, foreign_key="proyectos.id")
    tramo_id: int | None = Field(default=None, foreign_key="tramos.id")
    tipo_servicio_id: int | None = Field(
        default=None, foreign_key="tipos_servicio.id"
    )
    vehiculo_id: int | None = Field(default=None, foreign_key="activos.id")
    camabaja_id: int | None = Field(default=None, foreign_key="activos.id")
    kilometros: Decimal | None = Field(
        default=None, sa_column=Column(Numeric(12, 3), nullable=True)
    )
    hora_salida: time | None = Field(default=None)
    hora_llegada: time | None = Field(default=None)
    remision_agresur: str | None = Field(default=None)
    observaciones: str | None = Field(default=None, sa_column=Column(Text))
    usuario_creador_id: int = Field(foreign_key="usuarios.id")
    # NO_FACTURADA | FACTURADA_PARCIAL | FACTURADA | NO_APLICA ("No aplica
    # facturación": no cuenta como pendiente ni se puede facturar).
    estado_facturacion: str = Field(default="NO_FACTURADA")
    # Fecha y hora "IngRegistro" del Excel histórico (opcional).
    ing_registro: datetime | None = Field(default=None)
    creado_en: datetime = Field(default_factory=ahora_utc)
    actualizado_en: datetime = Field(
        default_factory=ahora_utc,
        sa_column_kwargs={"onupdate": ahora_utc},
    )


class RemisionProducto(SQLModel, table=True):
    __tablename__ = "remision_productos"
    __table_args__ = (Index("ix_remision_productos_remision_id", "remision_id"),)

    id: int | None = Field(default=None, primary_key=True)
    remision_id: int = Field(
        sa_column=Column(
            ForeignKey("remisiones.id", ondelete="CASCADE"), nullable=False
        )
    )
    # Opcionales solo por el histórico: hay filas del Excel sin producto o
    # sin cantidad. La app exige ambos al crear o editar un producto.
    producto_id: int | None = Field(default=None, foreign_key="productos.id")
    cantidad: Decimal | None = Field(default=None, sa_column=Column(Numeric(12, 3), nullable=True))
    unidad_medida_id: int | None = Field(
        default=None, foreign_key="unidades_medida.id"
    )
    valor_material: Decimal = Field(
        default=0, sa_column=Column(Numeric(14, 2), nullable=False)
    )
    valor_flete: Decimal = Field(
        default=0, sa_column=Column(Numeric(14, 2), nullable=False)
    )
    valor_camabaja: Decimal = Field(
        default=0, sa_column=Column(Numeric(14, 2), nullable=False)
    )
    # Opcional solo por el histórico (filas del Excel sin número de viajes).
    numero_viajes: int | None = Field(default=1)
    valor_comision: Decimal = Field(
        default=0, sa_column=Column(Numeric(14, 2), nullable=False)
    )
    valor_costo: Decimal = Field(
        default=0, sa_column=Column(Numeric(14, 2), nullable=False)
    )
