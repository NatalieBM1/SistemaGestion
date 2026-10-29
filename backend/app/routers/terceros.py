from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import literal
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlmodel import Session, func, or_, select

from app.core.database import get_session
from app.core.deps import require_permission
from app.core.errors import commit_or_409
from app.core.ordenamiento import clausulas_orden, texto_como_numero
from app.models.tercero import Tercero, TerceroTipo, TipoTercero
from app.models.ubicacion import Municipio
from app.schemas.common import PaginatedResponse
from app.schemas.tercero import (
    TerceroCreate,
    TerceroRead,
    TerceroTipoAsociar,
    TerceroUpdate,
)

router = APIRouter(prefix="/api/terceros", tags=["terceros"])


def _tipos_de_tercero(session: Session, tercero_id: int) -> list[str]:
    statement = (
        select(TipoTercero.nombre)
        .join(TerceroTipo, TerceroTipo.tipo_id == TipoTercero.id)
        .where(TerceroTipo.tercero_id == tercero_id)
    )
    return list(session.exec(statement).all())


def _serializar_tercero(session: Session, tercero: Tercero) -> TerceroRead:
    municipio = session.get(Municipio, tercero.municipio_id) if tercero.municipio_id else None
    return TerceroRead(
        id=tercero.id,
        identificacion=tercero.identificacion,
        nombre=tercero.nombre,
        direccion=tercero.direccion,
        municipio_id=tercero.municipio_id,
        municipio_nombre=municipio.nombre if municipio else None,
        email=tercero.email,
        telefono=tercero.telefono,
        regimen=tercero.regimen,
        tiene_licencia=tercero.tiene_licencia,
        fecha_vencimiento_licencia=tercero.fecha_vencimiento_licencia,
        creado_en=tercero.creado_en,
        tipos=_tipos_de_tercero(session, tercero.id),
    )


def _verificar_identificacion_unica(
    session: Session, identificacion: str | None, excluir_id: int | None = None
) -> None:
    if identificacion is None:
        return
    statement = select(Tercero).where(Tercero.identificacion == identificacion)
    if excluir_id is not None:
        statement = statement.where(Tercero.id != excluir_id)
    if session.exec(statement).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un tercero con identificacion '{identificacion}'",
        )


def _obtener_tercero_o_404(session: Session, tercero_id: int) -> Tercero:
    tercero = session.get(Tercero, tercero_id)
    if tercero is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el tercero con id {tercero_id}",
        )
    return tercero


COLUMNAS_ORDENABLES_TERCEROS = {"identificacion", "nombre", "telefono", "tipos", "municipio"}


@router.get(
    "",
    response_model=PaginatedResponse[TerceroRead],
    dependencies=[Depends(require_permission("terceros.leer"))],
)
def listar_terceros(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, description="Búsqueda por nombre o identificación"),
    tipo: str | None = Query(None, description="Filtrar por tipo, ej: cliente, conductor"),
    ordenar_por: str | None = Query(None),
    sentido: str = Query("asc", pattern="^(asc|desc)$"),
    session: Session = Depends(get_session),
):
    statement = select(Tercero)
    if q:
        statement = statement.where(
            or_(Tercero.nombre.ilike(f"%{q}%"), Tercero.identificacion.ilike(f"%{q}%"))
        )
    if tipo:
        statement = (
            statement.join(TerceroTipo, TerceroTipo.tercero_id == Tercero.id)
            .join(TipoTercero, TipoTercero.id == TerceroTipo.tipo_id)
            .where(func.lower(TipoTercero.nombre) == tipo.lower())
        )
    total = session.exec(select(func.count()).select_from(statement.subquery())).one()
    if ordenar_por:
        if ordenar_por not in COLUMNAS_ORDENABLES_TERCEROS:
            raise HTTPException(status_code=422, detail=f"No se puede ordenar terceros por '{ordenar_por}'.")
        if ordenar_por == "tipos":
            # Los tipos del tercero unidos alfabéticamente ("CLIENTE, CONDUCTOR").
            expresiones = [
                select(func.string_agg(TipoTercero.nombre, aggregate_order_by(literal(", "), TipoTercero.nombre)))
                .join(TerceroTipo, TerceroTipo.tipo_id == TipoTercero.id)
                .where(TerceroTipo.tercero_id == Tercero.id)
                .correlate(Tercero)
                .scalar_subquery()
            ]
        elif ordenar_por == "municipio":
            expresiones = [
                select(Municipio.nombre).where(Municipio.id == Tercero.municipio_id).scalar_subquery()
            ]
        elif ordenar_por == "nombre":
            expresiones = [Tercero.nombre]
        else:
            # identificacion y telefono son texto pero guardan números.
            expresiones = texto_como_numero(getattr(Tercero, ordenar_por))
        statement = statement.order_by(*clausulas_orden(expresiones, sentido, Tercero.id))
    else:
        statement = statement.order_by(Tercero.id)
    terceros = session.exec(
        statement.offset((page - 1) * page_size).limit(page_size)
    ).all()
    items = [_serializar_tercero(session, t) for t in terceros]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/{tercero_id}",
    response_model=TerceroRead,
    dependencies=[Depends(require_permission("terceros.leer"))],
)
def obtener_tercero(tercero_id: int, session: Session = Depends(get_session)):
    tercero = _obtener_tercero_o_404(session, tercero_id)
    return _serializar_tercero(session, tercero)


@router.post(
    "",
    response_model=TerceroRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("terceros.escribir"))],
)
def crear_tercero(payload: TerceroCreate, session: Session = Depends(get_session)):
    _verificar_identificacion_unica(session, payload.identificacion)
    datos = payload.model_dump()
    datos["nombre"] = datos["nombre"].upper()
    tercero = Tercero(**datos)
    session.add(tercero)
    commit_or_409(session)
    session.refresh(tercero)
    return _serializar_tercero(session, tercero)


@router.put(
    "/{tercero_id}",
    response_model=TerceroRead,
    dependencies=[Depends(require_permission("terceros.escribir"))],
)
def actualizar_tercero(
    tercero_id: int, payload: TerceroUpdate, session: Session = Depends(get_session)
):
    tercero = _obtener_tercero_o_404(session, tercero_id)
    datos = payload.model_dump(exclude_unset=True)
    _verificar_identificacion_unica(
        session, datos.get("identificacion"), excluir_id=tercero_id
    )
    if "nombre" in datos and datos["nombre"] is not None:
        datos["nombre"] = datos["nombre"].upper()
    for campo, valor in datos.items():
        setattr(tercero, campo, valor)
    session.add(tercero)
    commit_or_409(session)
    session.refresh(tercero)
    return _serializar_tercero(session, tercero)


@router.delete(
    "/{tercero_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("terceros.escribir"))],
)
def eliminar_tercero(tercero_id: int, session: Session = Depends(get_session)):
    tercero = _obtener_tercero_o_404(session, tercero_id)
    session.delete(tercero)
    commit_or_409(
        session,
        mensaje="No se puede eliminar el tercero: está referenciado por otros registros.",
    )


@router.post(
    "/{tercero_id}/tipos",
    response_model=TerceroRead,
    dependencies=[Depends(require_permission("terceros.escribir"))],
)
def asociar_tipo_a_tercero(
    tercero_id: int, payload: TerceroTipoAsociar, session: Session = Depends(get_session)
):
    tercero = _obtener_tercero_o_404(session, tercero_id)
    tipo = session.get(TipoTercero, payload.tipo_id)
    if tipo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el tipo de tercero con id {payload.tipo_id}",
        )
    existente = session.get(TerceroTipo, (tercero_id, payload.tipo_id))
    if existente is None:
        session.add(TerceroTipo(tercero_id=tercero_id, tipo_id=payload.tipo_id))
        commit_or_409(session)
    return _serializar_tercero(session, tercero)


@router.delete(
    "/{tercero_id}/tipos/{tipo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("terceros.escribir"))],
)
def desasociar_tipo_de_tercero(
    tercero_id: int, tipo_id: int, session: Session = Depends(get_session)
):
    _obtener_tercero_o_404(session, tercero_id)
    existente = session.get(TerceroTipo, (tercero_id, tipo_id))
    if existente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El tercero {tercero_id} no tiene asociado el tipo {tipo_id}.",
        )
    session.delete(existente)
    commit_or_409(session)
