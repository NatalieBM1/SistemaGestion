from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    email: str = Field(unique=True)
    password_hash: str
    activo: bool = Field(default=True)
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )


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
