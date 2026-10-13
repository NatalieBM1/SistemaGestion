from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, Numeric, Text
from sqlmodel import Field, SQLModel


class Remision(SQLModel, table=True):
    __tablename__ = "remisiones"
    __table_args__ = (
        CheckConstraint(
            "estado_facturacion IN ('NO_FACTURADA', 'FACTURADA_PARCIAL', 'FACTURADA')",
            name="ck_remisiones_estado_facturacion",
        ),
        Index("ix_remisiones_fecha", "fecha"),
        Index("ix_remisiones_cliente_id", "cliente_id"),
        Index("ix_remisiones_estado_facturacion", "estado_facturacion"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    numero_remision: str = Field(unique=True)
    prefijo_id: int = Field(foreign_key="prefijos.id")
    consecutivo: str
    orden_servicio_id: Optional[int] = Field(
        default=None, foreign_key="ordenes_servicio.id"
    )
    fecha: date
    forma_pago_id: Optional[int] = Field(default=None, foreign_key="formas_pago.id")
    cliente_id: int = Field(foreign_key="terceros.id")
    conductor_id: Optional[int] = Field(default=None, foreign_key="terceros.id")
    origen_municipio_id: int = Field(foreign_key="municipios.id")
    destino_municipio_id: int = Field(foreign_key="municipios.id")
    proyecto_id: Optional[int] = Field(default=None, foreign_key="proyectos.id")
    tramo_id: Optional[int] = Field(default=None, foreign_key="tramos.id")
    tipo_servicio_id: Optional[int] = Field(
        default=None, foreign_key="tipos_servicio.id"
    )
    vehiculo_id: Optional[int] = Field(default=None, foreign_key="activos.id")
    camabaja_id: Optional[int] = Field(default=None, foreign_key="activos.id")
    kilometros: Optional[Decimal] = Field(
        default=None, sa_column=Column(Numeric(12, 3), nullable=True)
    )
    hora_salida: Optional[time] = Field(default=None)
    hora_llegada: Optional[time] = Field(default=None)
    remision_agresur: Optional[str] = Field(default=None)
    observaciones: Optional[str] = Field(default=None, sa_column=Column(Text))
    usuario_creador_id: int = Field(foreign_key="usuarios.id")
    estado_facturacion: str = Field(default="NO_FACTURADA")
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )


class RemisionProducto(SQLModel, table=True):
    __tablename__ = "remision_productos"
    __table_args__ = (Index("ix_remision_productos_remision_id", "remision_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    remision_id: int = Field(
        sa_column=Column(
            ForeignKey("remisiones.id", ondelete="CASCADE"), nullable=False
        )
    )
    producto_id: int = Field(foreign_key="productos.id")
    cantidad: Decimal = Field(sa_column=Column(Numeric(12, 3), nullable=False))
    unidad_medida_id: Optional[int] = Field(
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
    numero_viajes: int = Field(default=1)
    valor_comision: Decimal = Field(
        default=0, sa_column=Column(Numeric(14, 2), nullable=False)
    )
    valor_costo: Decimal = Field(
        default=0, sa_column=Column(Numeric(14, 2), nullable=False)
    )
