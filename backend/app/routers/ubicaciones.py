from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, func, select

from app.core.database import get_session
from app.core.deps import require_permission
from app.core.errors import commit_or_409
from app.models.ubicacion import Departamento, Municipio
from app.schemas.common import PaginatedResponse
from app.schemas.ubicacion import (
    DepartamentoCreate,
    DepartamentoRead,
    DepartamentoUpdate,
    MunicipioCreate,
    MunicipioRead,
    MunicipioUpdate,
)

router = APIRouter(prefix="/api/ubicaciones", tags=["ubicaciones"])


def _verificar_codigo_dane_unico(
    session: Session, model, codigo_dane: str | None, excluir_id: int | None = None
) -> None:
    if codigo_dane is None:
        return
    statement = select(model).where(model.codigo_dane == codigo_dane)
    if excluir_id is not None:
        statement = statement.where(model.id != excluir_id)
    if session.exec(statement).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un registro con codigo_dane = '{codigo_dane}'",
        )


def _obtener_departamento_o_404(session: Session, departamento_id: int) -> Departamento:
    departamento = session.get(Departamento, departamento_id)
    if departamento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el departamento con id {departamento_id}",
        )
    return departamento


def _obtener_municipio_o_404(session: Session, municipio_id: int) -> Municipio:
    municipio = session.get(Municipio, municipio_id)
    if municipio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el municipio con id {municipio_id}",
        )
    return municipio


@router.get(
    "/departamentos",
    response_model=PaginatedResponse[DepartamentoRead],
    dependencies=[Depends(require_permission("ubicaciones.leer"))],
)
def listar_departamentos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, description="Búsqueda por nombre"),
    session: Session = Depends(get_session),
):
    statement = select(Departamento)
    if q:
        statement = statement.where(Departamento.nombre.ilike(f"%{q}%"))
    total = session.exec(select(func.count()).select_from(statement.subquery())).one()
    items = session.exec(
        statement.offset((page - 1) * page_size).limit(page_size)
    ).all()
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/departamentos/{departamento_id}",
    response_model=DepartamentoRead,
    dependencies=[Depends(require_permission("ubicaciones.leer"))],
)
def obtener_departamento(
    departamento_id: int, session: Session = Depends(get_session)
):
    return _obtener_departamento_o_404(session, departamento_id)


@router.post(
    "/departamentos",
    response_model=DepartamentoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("ubicaciones.escribir"))],
)
def crear_departamento(
    payload: DepartamentoCreate, session: Session = Depends(get_session)
):
    _verificar_codigo_dane_unico(session, Departamento, payload.codigo_dane)
    departamento = Departamento(**payload.model_dump())
    session.add(departamento)
    commit_or_409(session)
    session.refresh(departamento)
    return departamento


@router.put(
    "/departamentos/{departamento_id}",
    response_model=DepartamentoRead,
    dependencies=[Depends(require_permission("ubicaciones.escribir"))],
)
def actualizar_departamento(
    departamento_id: int,
    payload: DepartamentoUpdate,
    session: Session = Depends(get_session),
):
    departamento = _obtener_departamento_o_404(session, departamento_id)
    datos = payload.model_dump(exclude_unset=True)
    _verificar_codigo_dane_unico(
        session, Departamento, datos.get("codigo_dane"), excluir_id=departamento_id
    )
    for campo, valor in datos.items():
        setattr(departamento, campo, valor)
    session.add(departamento)
    commit_or_409(session)
    session.refresh(departamento)
    return departamento


@router.get(
    "/departamentos/{departamento_id}/municipios",
    response_model=PaginatedResponse[MunicipioRead],
    dependencies=[Depends(require_permission("ubicaciones.leer"))],
)
def listar_municipios_de_departamento(
    departamento_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, description="Búsqueda por nombre"),
    session: Session = Depends(get_session),
):
    _obtener_departamento_o_404(session, departamento_id)
    statement = select(Municipio).where(Municipio.departamento_id == departamento_id)
    if q:
        statement = statement.where(Municipio.nombre.ilike(f"%{q}%"))
    total = session.exec(select(func.count()).select_from(statement.subquery())).one()
    items = session.exec(
        statement.offset((page - 1) * page_size).limit(page_size)
    ).all()
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/municipios",
    response_model=PaginatedResponse[MunicipioRead],
    dependencies=[Depends(require_permission("ubicaciones.leer"))],
)
def listar_municipios(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, description="Búsqueda por nombre"),
    session: Session = Depends(get_session),
):
    statement = select(Municipio)
    if q:
        statement = statement.where(Municipio.nombre.ilike(f"%{q}%"))
    total = session.exec(select(func.count()).select_from(statement.subquery())).one()
    items = session.exec(
        statement.offset((page - 1) * page_size).limit(page_size)
    ).all()
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/municipios/{municipio_id}",
    response_model=MunicipioRead,
    dependencies=[Depends(require_permission("ubicaciones.leer"))],
)
def obtener_municipio(municipio_id: int, session: Session = Depends(get_session)):
    return _obtener_municipio_o_404(session, municipio_id)


@router.post(
    "/municipios",
    response_model=MunicipioRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("ubicaciones.escribir"))],
)
def crear_municipio(payload: MunicipioCreate, session: Session = Depends(get_session)):
    _obtener_departamento_o_404(session, payload.departamento_id)
    _verificar_codigo_dane_unico(session, Municipio, payload.codigo_dane)
    municipio = Municipio(**payload.model_dump())
    session.add(municipio)
    commit_or_409(session)
    session.refresh(municipio)
    return municipio


@router.put(
    "/municipios/{municipio_id}",
    response_model=MunicipioRead,
    dependencies=[Depends(require_permission("ubicaciones.escribir"))],
)
def actualizar_municipio(
    municipio_id: int, payload: MunicipioUpdate, session: Session = Depends(get_session)
):
    municipio = _obtener_municipio_o_404(session, municipio_id)
    datos = payload.model_dump(exclude_unset=True)
    if "departamento_id" in datos:
        _obtener_departamento_o_404(session, datos["departamento_id"])
    _verificar_codigo_dane_unico(
        session, Municipio, datos.get("codigo_dane"), excluir_id=municipio_id
    )
    for campo, valor in datos.items():
        setattr(municipio, campo, valor)
    session.add(municipio)
    commit_or_409(session)
    session.refresh(municipio)
    return municipio
