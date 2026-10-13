from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UsuarioCreate(BaseModel):
    nombre: str
    email: str
    password: str
    activo: bool = True


class UsuarioUpdate(BaseModel):
    nombre: str | None = None
    email: str | None = None
    password: str | None = None
    activo: bool | None = None


class UsuarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str
    activo: bool
    creado_en: datetime
    actualizado_en: datetime
    roles: list[str] = []


class RolCreate(BaseModel):
    nombre: str


class RolUpdate(BaseModel):
    nombre: str | None = None


class RolRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    permisos: list[str] = []


class PermisoCreate(BaseModel):
    codigo: str
    modulo: str


class PermisoUpdate(BaseModel):
    codigo: str | None = None
    modulo: str | None = None


class PermisoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    modulo: str


class AsignarRoles(BaseModel):
    roles_ids: list[int]


class AsignarPermisos(BaseModel):
    permisos_ids: list[int]
