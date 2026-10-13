from pydantic import BaseModel, ConfigDict


class PrefijoCreate(BaseModel):
    codigo: str
    consecutivo_actual: int = 0
    es_manual: bool = False


class PrefijoUpdate(BaseModel):
    codigo: str | None = None
    consecutivo_actual: int | None = None
    es_manual: bool | None = None


class PrefijoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    consecutivo_actual: int
    es_manual: bool


class FormaPagoCreate(BaseModel):
    nombre: str


class FormaPagoUpdate(BaseModel):
    nombre: str | None = None


class FormaPagoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class TipoServicioCreate(BaseModel):
    nombre: str


class TipoServicioUpdate(BaseModel):
    nombre: str | None = None


class TipoServicioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ProductoCreate(BaseModel):
    codigo: str | None = None
    nombre: str


class ProductoUpdate(BaseModel):
    codigo: str | None = None
    nombre: str | None = None


class ProductoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str | None
    nombre: str


class UnidadMedidaCreate(BaseModel):
    nombre: str


class UnidadMedidaUpdate(BaseModel):
    nombre: str | None = None


class UnidadMedidaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class PrefijoFacturaCreate(BaseModel):
    codigo: str


class PrefijoFacturaUpdate(BaseModel):
    codigo: str | None = None


class PrefijoFacturaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str


class TipoTerceroCreate(BaseModel):
    nombre: str


class TipoTerceroUpdate(BaseModel):
    nombre: str | None = None


class TipoTerceroRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ProyectoCreate(BaseModel):
    nombre: str
    cliente_id: int


class ProyectoUpdate(BaseModel):
    nombre: str | None = None
    cliente_id: int | None = None


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
