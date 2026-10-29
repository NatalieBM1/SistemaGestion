from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.core.fechas import ahora_utc


class Tercero(SQLModel, table=True):
    __tablename__ = "terceros"

    id: Optional[int] = Field(default=None, primary_key=True)
    identificacion: str = Field(unique=True)
    nombre: str
    direccion: Optional[str] = Field(default=None)
    municipio_id: Optional[int] = Field(default=None, foreign_key="municipios.id")
    email: Optional[str] = Field(default=None)
    telefono: Optional[str] = Field(default=None)
    regimen: Optional[str] = Field(default=None)
    tiene_licencia: Optional[bool] = Field(default=None)
    fecha_vencimiento_licencia: Optional[date] = Field(default=None)
    creado_en: datetime = Field(default_factory=ahora_utc)


class TipoTercero(SQLModel, table=True):
    __tablename__ = "tipos_tercero"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)


class TerceroTipo(SQLModel, table=True):
    __tablename__ = "tercero_tipos"

    tercero_id: int = Field(foreign_key="terceros.id", primary_key=True)
    tipo_id: int = Field(foreign_key="tipos_tercero.id", primary_key=True)
