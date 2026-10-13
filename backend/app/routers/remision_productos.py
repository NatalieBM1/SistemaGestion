from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.deps import require_permission
from app.core.errors import commit_or_409
from app.models.remision import Remision, RemisionProducto
from app.schemas.remision import (
    ProductoRemisionCreate,
    ProductoRemisionRead,
    ProductoRemisionResponse,
    ProductoRemisionUpdate,
)
from app.services import remision_service as svc

router = APIRouter(prefix="/api/remisiones/{remision_id}/productos", tags=["remision-productos"])


def _obtener_remision_o_404(session: Session, remision_id: int) -> Remision:
    remision = session.get(Remision, remision_id)
    if remision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró la remisión con id {remision_id}",
        )
    return remision


def _obtener_producto_o_404(
    session: Session, remision_id: int, producto_id: int
) -> RemisionProducto:
    producto = session.get(RemisionProducto, producto_id)
    if producto is None or producto.remision_id != remision_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el producto {producto_id} en la remisión {remision_id}",
        )
    return producto


@router.get(
    "",
    response_model=list[ProductoRemisionRead],
    dependencies=[Depends(require_permission("remisiones.leer"))],
)
def listar_productos_de_remision(remision_id: int, session: Session = Depends(get_session)):
    _obtener_remision_o_404(session, remision_id)
    productos = session.exec(
        select(RemisionProducto).where(RemisionProducto.remision_id == remision_id)
    ).all()
    return [svc.serializar_producto(session, p) for p in productos]


@router.post(
    "",
    response_model=ProductoRemisionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("remisiones.escribir"))],
)
def agregar_producto_a_remision(
    remision_id: int,
    payload: ProductoRemisionCreate,
    session: Session = Depends(get_session),
):
    remision = _obtener_remision_o_404(session, remision_id)
    svc.validar_remision_editable(remision)

    producto = RemisionProducto(remision_id=remision_id, **payload.model_dump())
    session.add(producto)

    alerta = None
    if remision.orden_servicio_id is not None and producto.valor_flete:
        alerta = svc.aplicar_delta_saldo_orden(
            session, remision.orden_servicio_id, producto.valor_flete
        )

    commit_or_409(session)
    session.refresh(producto)
    return ProductoRemisionResponse(
        producto=svc.serializar_producto(session, producto), alerta_saldo_bajo=alerta
    )


@router.put(
    "/{producto_id}",
    response_model=ProductoRemisionResponse,
    dependencies=[Depends(require_permission("remisiones.escribir"))],
)
def actualizar_producto_de_remision(
    remision_id: int,
    producto_id: int,
    payload: ProductoRemisionUpdate,
    session: Session = Depends(get_session),
):
    remision = _obtener_remision_o_404(session, remision_id)
    svc.validar_remision_editable(remision)
    producto = _obtener_producto_o_404(session, remision_id, producto_id)

    datos = payload.model_dump(exclude_unset=True)
    valor_flete_anterior = producto.valor_flete

    for campo, valor in datos.items():
        setattr(producto, campo, valor)
    session.add(producto)

    alerta = None
    if remision.orden_servicio_id is not None:
        nuevo_valor_flete = datos.get("valor_flete", valor_flete_anterior)
        delta = nuevo_valor_flete - valor_flete_anterior
        if delta != 0:
            alerta = svc.aplicar_delta_saldo_orden(session, remision.orden_servicio_id, delta)

    commit_or_409(session)
    session.refresh(producto)
    return ProductoRemisionResponse(
        producto=svc.serializar_producto(session, producto), alerta_saldo_bajo=alerta
    )


@router.delete(
    "/{producto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("remisiones.escribir"))],
)
def eliminar_producto_de_remision(
    remision_id: int, producto_id: int, session: Session = Depends(get_session)
):
    remision = _obtener_remision_o_404(session, remision_id)
    svc.validar_remision_editable(remision)
    producto = _obtener_producto_o_404(session, remision_id, producto_id)

    if remision.orden_servicio_id is not None and producto.valor_flete:
        svc.aplicar_delta_saldo_orden(session, remision.orden_servicio_id, -producto.valor_flete)

    session.delete(producto)
    commit_or_409(session)
