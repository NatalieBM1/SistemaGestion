from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class TerceroCreate(BaseModel):
    identificacion: str
    nombre: str
    direccion: str
    municipio_id: int
    email: str
    telefono: str
    regimen: str
    tiene_licencia: bool | None = None
    fecha_vencimiento_licencia: date | None = None


class TerceroUpdate(BaseModel):
    identificacion: str | None = None
    nombre: str | None = None
    direccion: str | None = None
    municipio_id: int | None = None
    email: str | None = None
    telefono: str | None = None
    regimen: str | None = None
    tiene_licencia: bool | None = None
    fecha_vencimiento_licencia: date | None = None


class TerceroRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    identificacion: str
    nombre: str
    direccion: str
    municipio_id: int
    municipio_nombre: str | None = None
    email: str
    telefono: str
    regimen: str
    tiene_licencia: bool | None
    fecha_vencimiento_licencia: date | None
    creado_en: datetime
    tipos: list[str] = []


class TerceroTipoAsociar(BaseModel):
    tipo_id: int
