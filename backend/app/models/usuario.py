from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.core.fechas import ahora_utc


class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    email: str = Field(unique=True)
    # Cédula / identificación del usuario (opcional). Es lo que sale en
    # "ID del usuario" / "ID usuario" / "ID usuario factura" de los reportes.
    identificacion: Optional[str] = Field(default=None, max_length=30)
    password_hash: str
    activo: bool = Field(default=True)
    creado_en: datetime = Field(default_factory=ahora_utc)
    actualizado_en: datetime = Field(
        default_factory=ahora_utc,
        sa_column_kwargs={"onupdate": ahora_utc},
    )
    # Recuperación de contraseña: código de 6 dígitos (guardado como HMAC,
    # ver core/security.py) + expiración + intentos fallidos con ese código.
    reset_token: Optional[str] = Field(default=None)
    reset_token_expires: Optional[datetime] = Field(default=None)
    reset_intentos: int = Field(default=0, sa_column_kwargs={"server_default": "0"})
    # Va dentro de cada JWT ("ver"). Subirla invalida todos los tokens ya
    # emitidos del usuario (reset de contraseña, cambio por el admin,
    # desactivación). Ver core/deps.py.
    token_version: int = Field(default=0, sa_column_kwargs={"server_default": "0"})


class Rol(SQLModel, table=True):
    __tablename__ = "roles"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)


class Permiso(SQLModel, table=True):
    __tablename__ = "permisos"

    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(unique=True)
    modulo: str


class RolPermiso(SQLModel, table=True):
    __tablename__ = "rol_permisos"

    rol_id: int = Field(foreign_key="roles.id", primary_key=True)
    permiso_id: int = Field(foreign_key="permisos.id", primary_key=True)


class UsuarioRol(SQLModel, table=True):
    __tablename__ = "usuario_roles"

    usuario_id: int = Field(foreign_key="usuarios.id", primary_key=True)
    rol_id: int = Field(foreign_key="roles.id", primary_key=True)
