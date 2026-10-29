from pydantic import BaseModel, ConfigDict, field_validator


def _m(v: str | None) -> str | None:
    """Strip + mayúsculas para campos de texto de catálogos."""
    if v is None:
        return None
    return v.strip().upper()


def _m_req(v: str) -> str:
    return v.strip().upper()


class PrefijoCreate(BaseModel):
    codigo: str
    consecutivo_actual: int = 0
    es_manual: bool = False

    @field_validator("codigo", mode="before")
    @classmethod
    def norm(cls, v: str) -> str:
        return _m_req(v)


class PrefijoUpdate(BaseModel):
    codigo: str | None = None
    consecutivo_actual: int | None = None
    es_manual: bool | None = None

    @field_validator("codigo", mode="before")
    @classmethod
    def norm(cls, v: str | None) -> str | None:
        return _m(v)


class PrefijoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    consecutivo_actual: int
    es_manual: bool


class FormaPagoCreate(BaseModel):
    nombre: str

    @field_validator("nombre", mode="before")
    @classmethod
    def norm(cls, v: str) -> str:
        return _m_req(v)


class FormaPagoUpdate(BaseModel):
    nombre: str | None = None

    @field_validator("nombre", mode="before")
    @classmethod
    def norm(cls, v: str | None) -> str | None:
        return _m(v)


class FormaPagoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class TipoServicioCreate(BaseModel):
    nombre: str

    @field_validator("nombre", mode="before")
    @classmethod
    def norm(cls, v: str) -> str:
        return _m_req(v)


class TipoServicioUpdate(BaseModel):
    nombre: str | None = None

    @field_validator("nombre", mode="before")
    @classmethod
    def norm(cls, v: str | None) -> str | None:
        return _m(v)


class TipoServicioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ProductoCreate(BaseModel):
    codigo: str | None = None
    nombre: str

    @field_validator("codigo", mode="before")
    @classmethod
    def norm_codigo(cls, v: str | None) -> str | None:
        return _m(v)

    @field_validator("nombre", mode="before")
    @classmethod
    def norm_nombre(cls, v: str) -> str:
        return _m_req(v)


class ProductoUpdate(BaseModel):
    codigo: str | None = None
    nombre: str | None = None

    @field_validator("codigo", "nombre", mode="before")
    @classmethod
    def norm(cls, v: str | None) -> str | None:
        return _m(v)


class ProductoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str | None
    nombre: str


class UnidadMedidaCreate(BaseModel):
    nombre: str

    @field_validator("nombre", mode="before")
    @classmethod
    def norm(cls, v: str) -> str:
        return _m_req(v)


class UnidadMedidaUpdate(BaseModel):
    nombre: str | None = None

    @field_validator("nombre", mode="before")
    @classmethod
    def norm(cls, v: str | None) -> str | None:
        return _m(v)


class UnidadMedidaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class PrefijoFacturaCreate(BaseModel):
    codigo: str

    @field_validator("codigo", mode="before")
    @classmethod
    def norm(cls, v: str) -> str:
        return _m_req(v)


class PrefijoFacturaUpdate(BaseModel):
    codigo: str | None = None

    @field_validator("codigo", mode="before")
    @classmethod
    def norm(cls, v: str | None) -> str | None:
        return _m(v)


class PrefijoFacturaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str


class TipoTerceroCreate(BaseModel):
    nombre: str

    @field_validator("nombre", mode="before")
    @classmethod
    def norm(cls, v: str) -> str:
        return _m_req(v)


class TipoTerceroUpdate(BaseModel):
    nombre: str | None = None

    @field_validator("nombre", mode="before")
    @classmethod
    def norm(cls, v: str | None) -> str | None:
        return _m(v)


class TipoTerceroRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ProyectoCreate(BaseModel):
    nombre: str
    cliente_id: int

    @field_validator("nombre", mode="before")
    @classmethod
    def norm(cls, v: str) -> str:
        return _m_req(v)


class ProyectoUpdate(BaseModel):
    nombre: str | None = None
    cliente_id: int | None = None

    @field_validator("nombre", mode="before")
    @classmethod
    def norm(cls, v: str | None) -> str | None:
        return _m(v)


class ProyectoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    cliente_id: int


class TramoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    proyecto_id: int
    nombre: str
    kilometros: float | None = None
