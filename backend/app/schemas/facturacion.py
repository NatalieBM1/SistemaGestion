from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class FacturarRemisionRequest(BaseModel):
    numero_factura: str
    fecha_factura: date
    tipo: Literal["TOTAL", "PARCIAL"]
    valor_facturado: Decimal | None = None


class FacturarRemisionResponse(BaseModel):
    remision_facturacion_id: int
    numero_factura: str
    tipo_facturacion: str
    valor_facturado: Decimal
    estado_facturacion: str
    valor_facturado_total: Decimal
    saldo_pendiente: Decimal


class ResumenFacturacionRemisionRead(BaseModel):
    remision_id: int
    valor_total: Decimal
    valor_facturado: Decimal
    saldo_pendiente: Decimal
    estado_facturacion: str


class ActualizarFacturaRequest(BaseModel):
    numero_factura_actual: str
    numero_factura_nuevo: str | None = None
    fecha_factura_nueva: date | None = None


class ActualizarFacturaResponse(BaseModel):
    numero_factura: str
    fecha_factura: date
    remisiones_afectadas: int
    remisiones_ids: list[int]


class CargaExcelResponse(BaseModel):
    filas_totales: int
    filas_exitosas: int
    filas_error: int
    detalle_errores: list[dict[str, Any]]


class ResumenFacturasRead(BaseModel):
    valor_total_facturado: Decimal
    cantidad_facturaciones: int


class FacturaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    numero_factura: str
    fecha_factura: date
    cantidad_remisiones: int
    valor_total_facturado: Decimal


class RemisionFacturacionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    remision_id: int
    numero_remision: str | None = None
    tipo_facturacion: str
    valor_facturado: Decimal
    anulada: bool
    anulada_en: datetime | None = None
    creado_en: datetime


class RemisionFacturacionHistorialRead(RemisionFacturacionRead):
    numero_factura: str
    fecha_factura: date
