from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class OrdenServicioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    cliente_id: int
    valor_tope: Decimal
    saldo_disponible: Decimal
