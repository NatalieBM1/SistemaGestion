from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator


def _mayus(v: str | None) -> str | None:
    """Strip + mayúsculas. Se aplica a nombre, dirección y régimen."""
    if v is None:
        return None
    return v.strip().upper()


class TerceroCreate(BaseModel):
    identificacion: str
    nombre: str
    direccion: str | None = None
    municipio_id: int | None = None
    email: str | None = None
    telefono: str | None = None
    regimen: str | None = None
    tiene_licencia: bool | None = None
    fecha_vencimiento_licencia: date | None = None

    @field_validator("nombre", mode="before")
    @classmethod
    def normalizar_nombre(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("direccion", "regimen", mode="before")
    @classmethod
    def normalizar_opcionales(cls, v: str | None) -> str | None:
        return _mayus(v)


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

    @field_validator("nombre", mode="before")
    @classmethod
    def normalizar_nombre(cls, v: str | None) -> str | None:
        return _mayus(v)

    @field_validator("direccion", "regimen", mode="before")
    @classmethod
    def normalizar_opcionales(cls, v: str | None) -> str | None:
        return _mayus(v)


class TerceroRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    identificacion: str
    nombre: str
    direccion: str | None
    municipio_id: int | None
    municipio_nombre: str | None = None
    email: str | None
    telefono: str | None
    regimen: str | None
    tiene_licencia: bool | None
    fecha_vencimiento_licencia: date | None
    creado_en: datetime
    tipos: list[str] = []


class TerceroTipoAsociar(BaseModel):
    tipo_id: int
