
from sqlmodel import Field, SQLModel


class Departamento(SQLModel, table=True):
    __tablename__ = "departamentos"

    id: int | None = Field(default=None, primary_key=True)
    codigo_dane: str = Field(unique=True)
    nombre: str


class Municipio(SQLModel, table=True):
    __tablename__ = "municipios"

    id: int | None = Field(default=None, primary_key=True)
    codigo_dane: str = Field(unique=True)
    nombre: str
    departamento_id: int = Field(foreign_key="departamentos.id")
