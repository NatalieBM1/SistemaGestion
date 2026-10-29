from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import CheckConstraint, Column, Index, Numeric
from sqlmodel import Field, SQLModel

from app.core.fechas import ahora_utc


class Factura(SQLModel, table=True):
    __tablename__ = "facturas"

    id: Optional[int] = Field(default=None, primary_key=True)
    numero_factura: str = Field(unique=True)
    fecha_factura: date
    creado_en: datetime = Field(default_factory=ahora_utc)


class RemisionFacturacion(SQLModel, table=True):
    __tablename__ = "remision_facturacion"
    __table_args__ = (
        CheckConstraint(
            "tipo_facturacion IN ('TOTAL', 'PARCIAL')",
            name="ck_remision_facturacion_tipo_facturacion",
        ),
        Index("ix_remision_facturacion_remision_id", "remision_id"),
        Index("ix_remision_facturacion_factura_id", "factura_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    remision_id: int = Field(foreign_key="remisiones.id")
    factura_id: int = Field(foreign_key="facturas.id")
    tipo_facturacion: str
    valor_facturado: Decimal = Field(sa_column=Column(Numeric(14, 2), nullable=False))
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuarios.id")
    anulada: bool = Field(default=False)
    anulada_en: Optional[datetime] = Field(default=None)
    creado_en: datetime = Field(default_factory=ahora_utc)
