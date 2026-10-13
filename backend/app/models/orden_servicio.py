from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Numeric
from sqlmodel import Field, SQLModel


class OrdenServicio(SQLModel, table=True):
    __tablename__ = "ordenes_servicio"

    id: Optional[int] = Field(default=None, primary_key=True)
    numero: str = Field(unique=True)
    cliente_id: int = Field(foreign_key="terceros.id")
    valor_tope: Decimal = Field(sa_column=Column(Numeric(14, 2), nullable=False))
    saldo_disponible: Decimal = Field(
        sa_column=Column(Numeric(14, 2), nullable=False)
    )
    creado_en: datetime = Field(default_factory=datetime.utcnow)
