from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, func, select

from app.core.database import get_session
from app.core.deps import require_permission
from app.core.errors import commit_or_409
from app.core.simple_crud import build_simple_crud_router
from app.models.activo import Activo, EmpresaGrupo
from app.schemas.activo import (
    ActivoCreate,
    ActivoRead,
    ActivoUpdate,
    EmpresaGrupoCreate,
    EmpresaGrupoRead,
    EmpresaGrupoUpdate,
)
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/api/activos", tags=["activos"])

empresas_router = build_simple_crud_router(
    model=EmpresaGrupo,
    create_schema=EmpresaGrupoCreate,
    update_schema=EmpresaGrupoUpdate,
    read_schema=EmpresaGrupoRead,
    prefix="/api/empresas",
    tag="empresas",
    unique_fields=["nombre"],
    search_field="nombre",
    read_permission="activos.leer",
    write_permission="activos.escribir",
)


def _verificar_placa_unica(
    session: Session, placa: str | None, excluir_id: int | None = None
) -> None:
    if placa is None:
        return
    statement = select(Activo).where(Activo.placa == placa)
    if excluir_id is not None:
        statement = statement.where(Activo.id != excluir_id)
    if session.exec(statement).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un activo con placa '{placa}'",
        )


def _obtener_activo_o_404(session: Session, activo_id: int) -> Activo:
    activo = session.get(Activo, activo_id)
    if activo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el activo con id {activo_id}",
        )
    return activo


def _serializar_activo(session: Session, activo: Activo) -> ActivoRead:
    empresa = session.get(EmpresaGrupo, activo.empresa_id)
    return ActivoRead(
        id=activo.id,
        placa=activo.placa,
        tipo_activo=activo.tipo_activo,
        clase=activo.clase,
        empresa_id=activo.empresa_id,
        empresa_nombre=empresa.nombre if empresa else None,
        es_segunda_mano=activo.es_segunda_mano,
        bloqueado=activo.bloqueado,
        creado_en=activo.creado_en,
    )


COLUMNAS_ORDENABLES_ACTIVOS = {"placa", "tipo_activo", "clase", "bloqueado"}


@router.get(
    "",
    response_model=PaginatedResponse[ActivoRead],
    dependencies=[Depends(require_permission("activos.leer"))],
)
def listar_activos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, description="Búsqueda por placa"),
    tipo_activo: str | None = Query(None, description="Filtrar por tipo_activo"),
    ordenar_por: str | None = Query(None),
    sentido: str = Query("asc", pattern="^(asc|desc)$"),
    session: Session = Depends(get_session),
):
    statement = select(Activo)
    if q:
        statement = statement.where(Activo.placa.ilike(f"%{q}%"))
    if tipo_activo:
        statement = statement.where(Activo.tipo_activo == tipo_activo)
    total = session.exec(select(func.count()).select_from(statement.subquery())).one()
    if ordenar_por:
        if ordenar_por not in COLUMNAS_ORDENABLES_ACTIVOS:
            raise HTTPException(status_code=422, detail=f"No se puede ordenar activos por '{ordenar_por}'.")
        columna = getattr(Activo, ordenar_por)
        statement = statement.order_by(columna.desc() if sentido == "desc" else columna.asc())
    activos = session.exec(
        statement.offset((page - 1) * page_size).limit(page_size)
    ).all()
    items = [_serializar_activo(session, a) for a in activos]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/{activo_id}",
    response_model=ActivoRead,
    dependencies=[Depends(require_permission("activos.leer"))],
)
def obtener_activo(activo_id: int, session: Session = Depends(get_session)):
    return _serializar_activo(session, _obtener_activo_o_404(session, activo_id))


@router.post(
    "",
    response_model=ActivoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("activos.escribir"))],
)
def crear_activo(payload: ActivoCreate, session: Session = Depends(get_session)):
    _verificar_placa_unica(session, payload.placa)
    activo = Activo(**payload.model_dump())
    session.add(activo)
    commit_or_409(session)
    session.refresh(activo)
    return _serializar_activo(session, activo)


@router.put(
    "/{activo_id}",
    response_model=ActivoRead,
    dependencies=[Depends(require_permission("activos.escribir"))],
)
def actualizar_activo(
    activo_id: int, payload: ActivoUpdate, session: Session = Depends(get_session)
):
    activo = _obtener_activo_o_404(session, activo_id)
    datos = payload.model_dump(exclude_unset=True)
    _verificar_placa_unica(session, datos.get("placa"), excluir_id=activo_id)
    for campo, valor in datos.items():
        setattr(activo, campo, valor)
    session.add(activo)
    commit_or_409(session)
    session.refresh(activo)
    return _serializar_activo(session, activo)


@router.delete(
    "/{activo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("activos.escribir"))],
)
def eliminar_activo(activo_id: int, session: Session = Depends(get_session)):
    activo = _obtener_activo_o_404(session, activo_id)
    session.delete(activo)
    commit_or_409(
        session,
        mensaje="No se puede eliminar el activo: está referenciado por otros registros.",
    )


@router.patch(
    "/{activo_id}/bloquear",
    response_model=ActivoRead,
    dependencies=[Depends(require_permission("activos.escribir"))],
)
def alternar_bloqueo_activo(activo_id: int, session: Session = Depends(get_session)):
    activo = _obtener_activo_o_404(session, activo_id)
    activo.bloqueado = not activo.bloqueado
    session.add(activo)
    commit_or_409(session)
    session.refresh(activo)
    return _serializar_activo(session, activo)
