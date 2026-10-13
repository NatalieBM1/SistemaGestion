from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EmpresaGrupoCreate(BaseModel):
    nombre: str


class EmpresaGrupoUpdate(BaseModel):
    nombre: str | None = None


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


class ActivoUpdate(BaseModel):
    placa: str | None = None
    tipo_activo: str | None = None
    clase: str | None = None
    empresa_id: int | None = None
    es_segunda_mano: bool | None = None
    bloqueado: bool | None = None


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
