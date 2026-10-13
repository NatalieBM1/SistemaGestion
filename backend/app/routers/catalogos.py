from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, func, select

from app.core.database import get_session
from app.core.deps import require_permission
from app.core.simple_crud import build_simple_crud_router
from app.models.catalogos import (
    FormaPago,
    Prefijo,
    PrefijoFactura,
    Producto,
    Proyecto,
    TipoServicio,
    Tramo,
    UnidadMedida,
)
from app.models.tercero import TipoTercero
from app.schemas.catalogos import (
    FormaPagoCreate,
    FormaPagoRead,
    FormaPagoUpdate,
    PrefijoCreate,
    PrefijoFacturaCreate,
    PrefijoFacturaRead,
    PrefijoFacturaUpdate,
    PrefijoRead,
    PrefijoUpdate,
    ProductoCreate,
    ProductoRead,
    ProductoUpdate,
    ProyectoCreate,
    ProyectoRead,
    ProyectoUpdate,
    TipoServicioCreate,
    TipoServicioRead,
    TipoServicioUpdate,
    TipoTerceroCreate,
    TipoTerceroRead,
    TipoTerceroUpdate,
    TramoRead,
    UnidadMedidaCreate,
    UnidadMedidaRead,
    UnidadMedidaUpdate,
)
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/api/catalogos")

router.include_router(
    build_simple_crud_router(
        model=Prefijo,
        create_schema=PrefijoCreate,
        update_schema=PrefijoUpdate,
        read_schema=PrefijoRead,
        prefix="/prefijos",
        tag="prefijos",
        unique_fields=["codigo"],
        search_field="codigo",
        read_permission="catalogos.leer",
        write_permission="catalogos.escribir",
    )
)

router.include_router(
    build_simple_crud_router(
        model=FormaPago,
        create_schema=FormaPagoCreate,
        update_schema=FormaPagoUpdate,
        read_schema=FormaPagoRead,
        prefix="/formas_pago",
        tag="formas_pago",
        unique_fields=["nombre"],
        search_field="nombre",
        read_permission="catalogos.leer",
        write_permission="catalogos.escribir",
    )
)

router.include_router(
    build_simple_crud_router(
        model=TipoServicio,
        create_schema=TipoServicioCreate,
        update_schema=TipoServicioUpdate,
        read_schema=TipoServicioRead,
        prefix="/tipos_servicio",
        tag="tipos_servicio",
        unique_fields=["nombre"],
        search_field="nombre",
        read_permission="catalogos.leer",
        write_permission="catalogos.escribir",
    )
)

router.include_router(
    build_simple_crud_router(
        model=Producto,
        create_schema=ProductoCreate,
        update_schema=ProductoUpdate,
        read_schema=ProductoRead,
        prefix="/productos",
        tag="productos",
        unique_fields=["codigo", "nombre"],
        search_field="nombre",
        read_permission="catalogos.leer",
        write_permission="catalogos.escribir",
    )
)

router.include_router(
    build_simple_crud_router(
        model=UnidadMedida,
        create_schema=UnidadMedidaCreate,
        update_schema=UnidadMedidaUpdate,
        read_schema=UnidadMedidaRead,
        prefix="/unidades_medida",
        tag="unidades_medida",
        unique_fields=["nombre"],
        search_field="nombre",
        read_permission="catalogos.leer",
        write_permission="catalogos.escribir",
    )
)

router.include_router(
    build_simple_crud_router(
        model=PrefijoFactura,
        create_schema=PrefijoFacturaCreate,
        update_schema=PrefijoFacturaUpdate,
        read_schema=PrefijoFacturaRead,
        prefix="/prefijos_factura",
        tag="prefijos_factura",
        unique_fields=["codigo"],
        search_field="codigo",
        read_permission="catalogos.leer",
        write_permission="catalogos.escribir",
    )
)

router.include_router(
    build_simple_crud_router(
        model=TipoTercero,
        create_schema=TipoTerceroCreate,
        update_schema=TipoTerceroUpdate,
        read_schema=TipoTerceroRead,
        prefix="/tipos_tercero",
        tag="tipos_tercero",
        unique_fields=["nombre"],
        search_field="nombre",
        read_permission="catalogos.leer",
        write_permission="catalogos.escribir",
    )
)

router.include_router(
    build_simple_crud_router(
        model=Proyecto,
        create_schema=ProyectoCreate,
        update_schema=ProyectoUpdate,
        read_schema=ProyectoRead,
        prefix="/proyectos",
        tag="proyectos",
        unique_fields=[],
        search_field="nombre",
        read_permission="catalogos.leer",
        write_permission="catalogos.escribir",
    )
)


@router.get(
    "/tramos",
    response_model=PaginatedResponse[TramoRead],
    tags=["tramos"],
    dependencies=[Depends(require_permission("catalogos.leer"))],
)
def listar_tramos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    proyecto_id: int | None = Query(None, description="Filtrar por proyecto"),
    q: str | None = Query(None, description="Búsqueda por nombre"),
    session: Session = Depends(get_session),
):
    statement = select(Tramo)
    if proyecto_id:
        statement = statement.where(Tramo.proyecto_id == proyecto_id)
    if q:
        statement = statement.where(Tramo.nombre.ilike(f"%{q}%"))
    total = session.exec(select(func.count()).select_from(statement.subquery())).one()
    items = session.exec(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/tramos/{tramo_id}",
    response_model=TramoRead,
    tags=["tramos"],
    dependencies=[Depends(require_permission("catalogos.leer"))],
)
def obtener_tramo(tramo_id: int, session: Session = Depends(get_session)):
    tramo = session.get(Tramo, tramo_id)
    if tramo is None:
        raise HTTPException(status_code=404, detail="Tramo no encontrado.")
    return tramo
