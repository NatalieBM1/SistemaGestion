from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class Auditoria(SQLModel, table=True):
    __tablename__ = "auditoria"
    __table_args__ = (
        Index("ix_auditoria_tabla_registro_id", "tabla", "registro_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    tabla: str
    registro_id: int
    accion: str
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuarios.id")
    detalle_json: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSONB)
    )
    creado_en: datetime = Field(default_factory=datetime.utcnow)


class CargaExcel(SQLModel, table=True):
    __tablename__ = "cargas_excel"

    id: Optional[int] = Field(default=None, primary_key=True)
    tipo: str
    nombre_archivo: Optional[str] = Field(default=None)
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuarios.id")
    filas_totales: Optional[int] = Field(default=None)
    filas_exitosas: Optional[int] = Field(default=None)
    filas_error: Optional[int] = Field(default=None)
    detalle_errores: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSONB)
    )
    creado_en: datetime = Field(default_factory=datetime.utcnow)
