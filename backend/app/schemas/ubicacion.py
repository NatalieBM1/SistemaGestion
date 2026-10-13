from pydantic import BaseModel, ConfigDict


class DepartamentoCreate(BaseModel):
    codigo_dane: str
    nombre: str


class DepartamentoUpdate(BaseModel):
    codigo_dane: str | None = None
    nombre: str | None = None


class DepartamentoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo_dane: str
    nombre: str


class MunicipioCreate(BaseModel):
    codigo_dane: str
    nombre: str
    departamento_id: int


class MunicipioUpdate(BaseModel):
    codigo_dane: str | None = None
    nombre: str | None = None
    departamento_id: int | None = None


class MunicipioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo_dane: str
    nombre: str
    departamento_id: int
