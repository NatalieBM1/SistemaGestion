from datetime import datetime
from typing import Any

from sqlalchemy import Column, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.core.fechas import ahora_utc


class Auditoria(SQLModel, table=True):
    __tablename__ = "auditoria"
    __table_args__ = (
        Index("ix_auditoria_tabla_registro_id", "tabla", "registro_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    tabla: str
    registro_id: int
    accion: str
    usuario_id: int | None = Field(default=None, foreign_key="usuarios.id")
    detalle_json: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSONB)
    )
    creado_en: datetime = Field(default_factory=ahora_utc)


class CargaExcel(SQLModel, table=True):
    __tablename__ = "cargas_excel"

    id: int | None = Field(default=None, primary_key=True)
    tipo: str
    nombre_archivo: str | None = Field(default=None)
    usuario_id: int | None = Field(default=None, foreign_key="usuarios.id")
    filas_totales: int | None = Field(default=None)
    filas_exitosas: int | None = Field(default=None)
    filas_error: int | None = Field(default=None)
    detalle_errores: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB)
    )
    creado_en: datetime = Field(default_factory=ahora_utc)
