from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class RemisionCreate(BaseModel):
    numero_remision: str | None = None
    prefijo_id: int
    orden_servicio_id: int | None = None
    fecha: date
    forma_pago_id: int | None = None
    cliente_id: int
    conductor_id: int | None = None
    origen_municipio_id: int
    destino_municipio_id: int
    proyecto_id: int | None = None
    tramo_id: int | None = None
    tipo_servicio_id: int | None = None
    vehiculo_id: int | None = None
    camabaja_id: int | None = None
    kilometros: Decimal | None = None
    hora_salida: time | None = None
    hora_llegada: time | None = None
    remision_agresur: str | None = None
    observaciones: str | None = None


class RemisionUpdate(BaseModel):
    orden_servicio_id: int | None = None
    fecha: date | None = None
    forma_pago_id: int | None = None
    cliente_id: int | None = None
    conductor_id: int | None = None
    origen_municipio_id: int | None = None
    destino_municipio_id: int | None = None
    proyecto_id: int | None = None
    tramo_id: int | None = None
    tipo_servicio_id: int | None = None
    vehiculo_id: int | None = None
    camabaja_id: int | None = None
    kilometros: Decimal | None = None
    hora_salida: time | None = None
    hora_llegada: time | None = None
    remision_agresur: str | None = None
    observaciones: str | None = None


class RemisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero_remision: str
    prefijo_id: int
    consecutivo: str
    orden_servicio_id: int | None
    fecha: date
    forma_pago_id: int | None
    cliente_id: int
    cliente_nombre: str | None = None
    conductor_id: int | None
    conductor_nombre: str | None = None
    origen_municipio_id: int
    origen_municipio_nombre: str | None = None
    destino_municipio_id: int
    destino_municipio_nombre: str | None = None
    proyecto_id: int | None
    tramo_id: int | None
    tipo_servicio_id: int | None
    vehiculo_id: int | None
    vehiculo_placa: str | None = None
    camabaja_id: int | None
    kilometros: Decimal | None
    hora_salida: time | None
    hora_llegada: time | None
    remision_agresur: str | None
    observaciones: str | None
    usuario_creador_id: int
    estado_facturacion: str
    valor_total: Decimal = Decimal(0)
    creado_en: datetime
    actualizado_en: datetime


class ProductoRemisionCreate(BaseModel):
    producto_id: int
    cantidad: Decimal
    unidad_medida_id: int | None = None
    valor_material: Decimal = Decimal(0)
    valor_flete: Decimal = Decimal(0)
    valor_camabaja: Decimal = Decimal(0)
    numero_viajes: int = 1
    valor_comision: Decimal = Decimal(0)
    valor_costo: Decimal = Decimal(0)


class ProductoRemisionUpdate(BaseModel):
    producto_id: int | None = None
    cantidad: Decimal | None = None
    unidad_medida_id: int | None = None
    valor_material: Decimal | None = None
    valor_flete: Decimal | None = None
    valor_camabaja: Decimal | None = None
    numero_viajes: int | None = None
    valor_comision: Decimal | None = None
    valor_costo: Decimal | None = None


class ProductoRemisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    remision_id: int
    producto_id: int
    producto_nombre: str | None = None
    cantidad: Decimal
    unidad_medida_id: int | None
    unidad_medida_nombre: str | None = None
    valor_material: Decimal
    valor_flete: Decimal
    valor_camabaja: Decimal
    numero_viajes: int
    valor_comision: Decimal
    valor_costo: Decimal


class RemisionDetalleRead(RemisionRead):
    productos: list[ProductoRemisionRead] = []


class RemisionUpdateResponse(BaseModel):
    remision: RemisionRead
    advertencia: str | None = None


class ProductoRemisionResponse(BaseModel):
    producto: ProductoRemisionRead
    alerta_saldo_bajo: str | None = None


class CopiarRemisionRequest(BaseModel):
    copiar_productos: bool = False


class CopiarRemisionResponse(BaseModel):
    remision: RemisionDetalleRead
    alerta_saldo_bajo: str | None = None
