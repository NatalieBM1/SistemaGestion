from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class EmpresaGrupo(SQLModel, table=True):
    __tablename__ = "empresas_grupo"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)


class Activo(SQLModel, table=True):
    __tablename__ = "activos"

    id: Optional[int] = Field(default=None, primary_key=True)
    placa: str = Field(unique=True)
    tipo_activo: str
    clase: str
    empresa_id: int = Field(foreign_key="empresas_grupo.id")
    es_segunda_mano: bool = Field(default=False)
    bloqueado: bool = Field(default=False)
    creado_en: datetime = Field(default_factory=datetime.utcnow)
