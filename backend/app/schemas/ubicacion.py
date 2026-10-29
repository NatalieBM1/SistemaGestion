from pydantic import BaseModel, ConfigDict, field_validator


def _m(v: str | None) -> str | None:
    if v is None:
        return None
    return v.strip().upper()


def _m_req(v: str) -> str:
    return v.strip().upper()


class DepartamentoCreate(BaseModel):
    codigo_dane: str
    nombre: str

    @field_validator("codigo_dane", "nombre", mode="before")
    @classmethod
    def norm(cls, v: str) -> str:
        return _m_req(v)


class DepartamentoUpdate(BaseModel):
    codigo_dane: str | None = None
    nombre: str | None = None

    @field_validator("codigo_dane", "nombre", mode="before")
    @classmethod
    def norm(cls, v: str | None) -> str | None:
        return _m(v)


class DepartamentoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo_dane: str
    nombre: str


class MunicipioCreate(BaseModel):
    codigo_dane: str
    nombre: str
    departamento_id: int

    @field_validator("codigo_dane", "nombre", mode="before")
    @classmethod
    def norm(cls, v: str) -> str:
        return _m_req(v)


class MunicipioUpdate(BaseModel):
    codigo_dane: str | None = None
    nombre: str | None = None
    departamento_id: int | None = None

    @field_validator("codigo_dane", "nombre", mode="before")
    @classmethod
    def norm(cls, v: str | None) -> str | None:
        return _m(v)


class MunicipioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo_dane: str
    nombre: str
    departamento_id: int
    departamento_nombre: str | None = None
    presentacion: str | None = None
