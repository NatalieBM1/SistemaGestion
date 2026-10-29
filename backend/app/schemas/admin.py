import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

_IDENTIFICACION = re.compile(r"^[0-9A-Za-z.\-]{1,30}$")


def _limpiar_identificacion(valor: str | None) -> str | None:
    """Opcional: vacío = sin dato. Cédula/NIT tal cual (texto, conserva
    ceros a la izquierda): dígitos, letras, punto o guion, hasta 30."""
    if valor is None:
        return None
    valor = valor.strip()
    if not valor:
        return None
    if not _IDENTIFICACION.match(valor):
        raise ValueError(
            "La identificación solo puede tener números, letras, punto o guion "
            "(máximo 30 caracteres)."
        )
    return valor


class UsuarioCreate(BaseModel):
    nombre: str
    email: str
    password: str
    activo: bool = True
    identificacion: str | None = None

    _validar_identificacion = field_validator("identificacion")(_limpiar_identificacion)


class UsuarioUpdate(BaseModel):
    nombre: str | None = None
    email: str | None = None
    password: str | None = None
    activo: bool | None = None
    identificacion: str | None = None

    _validar_identificacion = field_validator("identificacion")(_limpiar_identificacion)


class UsuarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str
    identificacion: str | None = None
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
