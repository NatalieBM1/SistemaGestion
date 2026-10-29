from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


def _m(v: str | None) -> str | None:
    if v is None:
        return None
    return v.strip().upper()


def _m_req(v: str) -> str:
    return v.strip().upper()


class EmpresaGrupoCreate(BaseModel):
    nombre: str

    @field_validator("nombre", mode="before")
    @classmethod
    def norm(cls, v: str) -> str:
        return _m_req(v)


class EmpresaGrupoUpdate(BaseModel):
    nombre: str | None = None

    @field_validator("nombre", mode="before")
    @classmethod
    def norm(cls, v: str | None) -> str | None:
        return _m(v)


class EmpresaGrupoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ActivoCreate(BaseModel):
    placa: str
    tipo_activo: str
    clase: str
    empresa_id: int
    es_segunda_mano: bool = False
    bloqueado: bool = False

    @field_validator("placa", "tipo_activo", "clase", mode="before")
    @classmethod
    def norm(cls, v: str) -> str:
        return _m_req(v)


class ActivoUpdate(BaseModel):
    placa: str | None = None
    tipo_activo: str | None = None
    clase: str | None = None
    empresa_id: int | None = None
    es_segunda_mano: bool | None = None
    bloqueado: bool | None = None

    @field_validator("placa", "tipo_activo", "clase", mode="before")
    @classmethod
    def norm(cls, v: str | None) -> str | None:
        return _m(v)


class ActivoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    placa: str
    tipo_activo: str
    clase: str
    empresa_id: int
    empresa_nombre: str | None = None
    es_segunda_mano: bool
    bloqueado: bool
    creado_en: datetime
