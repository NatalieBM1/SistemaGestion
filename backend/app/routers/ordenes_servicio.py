from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, func, select

from app.core.database import get_session
from app.core.deps import require_permission
from app.models.orden_servicio import OrdenServicio
from app.schemas.common import PaginatedResponse
from app.schemas.orden_servicio import OrdenServicioRead

router = APIRouter(prefix="/api/ordenes-servicio", tags=["ordenes-servicio"])


@router.get(
    "",
    response_model=PaginatedResponse[OrdenServicioRead],
    dependencies=[Depends(require_permission("remisiones.leer"))],
)
def listar_ordenes_servicio(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, description="Búsqueda por número de orden"),
    cliente_id: int | None = Query(None),
    session: Session = Depends(get_session),
):
    statement = select(OrdenServicio)
    if q:
        statement = statement.where(OrdenServicio.numero.ilike(f"%{q}%"))
    if cliente_id:
        statement = statement.where(OrdenServicio.cliente_id == cliente_id)
    total = session.exec(select(func.count()).select_from(statement.subquery())).one()
    items = session.exec(
        statement.order_by(OrdenServicio.numero).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/{orden_servicio_id}",
    response_model=OrdenServicioRead,
    dependencies=[Depends(require_permission("remisiones.leer"))],
)
def obtener_orden_servicio(orden_servicio_id: int, session: Session = Depends(get_session)):
    orden = session.get(OrdenServicio, orden_servicio_id)
    if orden is None:
        raise HTTPException(status_code=404, detail="Orden de servicio no encontrada.")
    return orden
