from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Session, SQLModel, func, select

from app.core.database import get_session
from app.core.deps import require_permission
from app.core.errors import commit_or_409
from app.schemas.common import PaginatedResponse


def build_simple_crud_router(
    *,
    model: type[SQLModel],
    create_schema: type[BaseModel],
    update_schema: type[BaseModel],
    read_schema: type[BaseModel],
    prefix: str,
    tag: str,
    unique_fields: list[str],
    search_field: str | None = None,
    read_permission: str | None = None,
    write_permission: str | None = None,
    create_permission: str | None = None,
    update_permission: str | None = None,
    delete_permission: str | None = None,
    sortable_fields: list[str] | None = None,
) -> APIRouter:
    """`write_permission` sigue gobernando crear/editar/eliminar cuando no
    se dan permisos más específicos — así los catálogos que no necesitan
    distinguir (ej. Proyectos) no cambian de comportamiento. Para separar
    "solo crear" de "editar"/"eliminar" (rol Operador en Catálogos), pasa
    `create_permission`/`update_permission`/`delete_permission`: cada uno
    reemplaza a `write_permission` solo para esa operación."""
    router = APIRouter(prefix=prefix, tags=[tag])
    nombre_singular = tag.rstrip("s")
    # Lista blanca de columnas por las que se puede ordenar (bloque A): por
    # defecto, todas las columnas propias del modelo — nunca se interpola
    # texto del usuario directo en el ORDER BY, siempre se valida contra
    # esta lista antes de usar getattr().
    campos_ordenables = set(sortable_fields) if sortable_fields is not None else set(model.model_fields.keys())
    read_deps = [Depends(require_permission(read_permission))] if read_permission else []
    create_deps = [Depends(require_permission(create_permission or write_permission))] if (create_permission or write_permission) else []
    update_deps = [Depends(require_permission(update_permission or write_permission))] if (update_permission or write_permission) else []
    delete_deps = [Depends(require_permission(delete_permission or write_permission))] if (delete_permission or write_permission) else []

    def _verificar_unicidad(
        session: Session, datos: dict, excluir_id: int | None = None
    ) -> None:
        for campo in unique_fields:
            valor = datos.get(campo)
            if valor is None:
                continue
            statement = select(model).where(getattr(model, campo) == valor)
            if excluir_id is not None:
                statement = statement.where(model.id != excluir_id)
            if session.exec(statement).first() is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe un registro de {nombre_singular} con {campo} = '{valor}'",
                )

    def _obtener_o_404(session: Session, item_id: int) -> SQLModel:
        obj = session.get(model, item_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró {nombre_singular} con id {item_id}",
            )
        return obj

    @router.get("", response_model=PaginatedResponse[read_schema], dependencies=read_deps)
    def listar(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        q: str | None = Query(None, description="Búsqueda por texto"),
        ordenar_por: str | None = Query(None, description="Columna por la que ordenar"),
        sentido: str = Query("asc", pattern="^(asc|desc)$"),
        session: Session = Depends(get_session),
    ):
        statement = select(model)
        if q and search_field:
            statement = statement.where(getattr(model, search_field).ilike(f"%{q}%"))
        if ordenar_por:
            if ordenar_por not in campos_ordenables:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"No se puede ordenar {nombre_singular} por '{ordenar_por}'.",
                )
            columna = getattr(model, ordenar_por)
            statement = statement.order_by(columna.desc() if sentido == "desc" else columna.asc())
        total = session.exec(
            select(func.count()).select_from(statement.subquery())
        ).one()
        items = session.exec(
            statement.offset((page - 1) * page_size).limit(page_size)
        ).all()
        return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)

    @router.get("/{item_id}", response_model=read_schema, dependencies=read_deps)
    def obtener(item_id: int, session: Session = Depends(get_session)):
        return _obtener_o_404(session, item_id)

    @router.post(
        "",
        response_model=read_schema,
        status_code=status.HTTP_201_CREATED,
        dependencies=create_deps,
    )
    def crear(payload: create_schema, session: Session = Depends(get_session)):
        datos = payload.model_dump()
        _verificar_unicidad(session, datos)
        obj = model(**datos)
        session.add(obj)
        commit_or_409(session)
        session.refresh(obj)
        return obj

    @router.put("/{item_id}", response_model=read_schema, dependencies=update_deps)
    def actualizar(
        item_id: int, payload: update_schema, session: Session = Depends(get_session)
    ):
        obj = _obtener_o_404(session, item_id)
        datos = payload.model_dump(exclude_unset=True)
        _verificar_unicidad(session, datos, excluir_id=item_id)
        for campo, valor in datos.items():
            setattr(obj, campo, valor)
        session.add(obj)
        commit_or_409(session)
        session.refresh(obj)
        return obj

    @router.delete(
        "/{item_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=delete_deps
    )
    def eliminar(item_id: int, session: Session = Depends(get_session)):
        obj = _obtener_o_404(session, item_id)
        session.delete(obj)
        commit_or_409(
            session,
            mensaje=f"No se puede eliminar {nombre_singular}: está referenciado por otros registros.",
        )

    return router
