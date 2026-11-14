from decimal import Decimal

from sqlalchemy import Column, Numeric
from sqlmodel import Field, SQLModel


class Prefijo(SQLModel, table=True):
    __tablename__ = "prefijos"

    id: int | None = Field(default=None, primary_key=True)
    codigo: str = Field(unique=True)
    consecutivo_actual: int = Field(default=0)
    es_manual: bool = Field(default=False)


class FormaPago(SQLModel, table=True):
    __tablename__ = "formas_pago"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)


class TipoServicio(SQLModel, table=True):
    __tablename__ = "tipos_servicio"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)


class Producto(SQLModel, table=True):
    __tablename__ = "productos"

    id: int | None = Field(default=None, primary_key=True)
    codigo: str | None = Field(default=None, unique=True)
    nombre: str = Field(unique=True)


class UnidadMedida(SQLModel, table=True):
    __tablename__ = "unidades_medida"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)


class Proyecto(SQLModel, table=True):
    __tablename__ = "proyectos"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str
    cliente_id: int = Field(foreign_key="terceros.id")


class Tramo(SQLModel, table=True):
    __tablename__ = "tramos"

    id: int | None = Field(default=None, primary_key=True)
    proyecto_id: int = Field(foreign_key="proyectos.id")
    nombre: str
    kilometros: Decimal | None = Field(
        default=None, sa_column=Column(Numeric(12, 3), nullable=True)
    )


class PrefijoFactura(SQLModel, table=True):
    __tablename__ = "prefijos_factura"

    id: int | None = Field(default=None, primary_key=True)
    codigo: str = Field(unique=True)
