from typing import Optional

from sqlmodel import Field, SQLModel


class Departamento(SQLModel, table=True):
    __tablename__ = "departamentos"

    id: Optional[int] = Field(default=None, primary_key=True)
    codigo_dane: str = Field(unique=True)
    nombre: str


class Municipio(SQLModel, table=True):
    __tablename__ = "municipios"

    id: Optional[int] = Field(default=None, primary_key=True)
    codigo_dane: str = Field(unique=True)
    nombre: str
    departamento_id: int = Field(foreign_key="departamentos.id")
