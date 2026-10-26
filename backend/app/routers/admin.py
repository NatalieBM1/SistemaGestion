from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, func, or_, select

from app.core.database import get_session
from app.core.deps import require_permission
from app.core.errors import commit_or_409
from app.core.security import hash_password
from app.core.simple_crud import build_simple_crud_router
from app.models.usuario import Permiso, Rol, RolPermiso, Usuario, UsuarioRol
from app.schemas.admin import (
    AsignarPermisos,
    AsignarRoles,
    PermisoCreate,
    PermisoRead,
    PermisoUpdate,
    RolCreate,
    RolRead,
    RolUpdate,
    UsuarioCreate,
    UsuarioRead,
    UsuarioUpdate,
)
from app.schemas.common import PaginatedResponse
from app.services import admin_service as svc

ADMIN_PERMISO = "usuarios.administrar"

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_permission(ADMIN_PERMISO))],
)

permisos_router = build_simple_crud_router(
    model=Permiso,
    create_schema=PermisoCreate,
    update_schema=PermisoUpdate,
    read_schema=PermisoRead,
    prefix="/api/admin/permisos",
    tag="permisos",
    unique_fields=["codigo"],
    search_field="codigo",
    read_permission=ADMIN_PERMISO,
    write_permission=ADMIN_PERMISO,
)


# --- helpers ---


def _roles_de_usuario(session: Session, usuario_id: int) -> list[str]:
    statement = (
        select(Rol.nombre)
        .join(UsuarioRol, UsuarioRol.rol_id == Rol.id)
        .where(UsuarioRol.usuario_id == usuario_id)
    )
    return list(session.exec(statement).all())


def _serializar_usuario(session: Session, usuario: Usuario) -> UsuarioRead:
    return UsuarioRead(
        id=usuario.id,
        nombre=usuario.nombre,
        email=usuario.email,
        activo=usuario.activo,
        creado_en=usuario.creado_en,
        actualizado_en=usuario.actualizado_en,
        roles=_roles_de_usuario(session, usuario.id),
    )


def _permisos_de_rol(session: Session, rol_id: int) -> list[str]:
    statement = (
        select(Permiso.codigo)
        .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
        .where(RolPermiso.rol_id == rol_id)
    )
    return list(session.exec(statement).all())


def _serializar_rol(session: Session, rol: Rol) -> RolRead:
    return RolRead(id=rol.id, nombre=rol.nombre, permisos=_permisos_de_rol(session, rol.id))


def _obtener_usuario_o_404(session: Session, usuario_id: int) -> Usuario:
    usuario = session.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el usuario con id {usuario_id}",
        )
    return usuario


def _obtener_rol_o_404(session: Session, rol_id: int) -> Rol:
    rol = session.get(Rol, rol_id)
    if rol is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el rol con id {rol_id}",
        )
    return rol


def _verificar_email_unico(
    session: Session, email: str | None, excluir_id: int | None = None
) -> None:
    if email is None:
        return
    statement = select(Usuario).where(Usuario.email == email)
    if excluir_id is not None:
        statement = statement.where(Usuario.id != excluir_id)
    if session.exec(statement).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un usuario con email '{email}'",
        )


def _verificar_nombre_rol_unico(
    session: Session, nombre: str | None, excluir_id: int | None = None
) -> None:
    if nombre is None:
        return
    statement = select(Rol).where(Rol.nombre == nombre)
    if excluir_id is not None:
        statement = statement.where(Rol.id != excluir_id)
    if session.exec(statement).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un rol con nombre '{nombre}'",
        )


# --- usuarios ---


COLUMNAS_ORDENABLES_USUARIOS = {"nombre", "email", "activo"}


@router.get("/usuarios", response_model=PaginatedResponse[UsuarioRead])
def listar_usuarios(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, description="Búsqueda por nombre o email"),
    ordenar_por: str | None = Query(None),
    sentido: str = Query("asc", pattern="^(asc|desc)$"),
    session: Session = Depends(get_session),
):
    statement = select(Usuario)
    if q:
        statement = statement.where(
            or_(Usuario.nombre.ilike(f"%{q}%"), Usuario.email.ilike(f"%{q}%"))
        )
    total = session.exec(select(func.count()).select_from(statement.subquery())).one()
    if ordenar_por:
        if ordenar_por not in COLUMNAS_ORDENABLES_USUARIOS:
            raise HTTPException(status_code=422, detail=f"No se puede ordenar usuarios por '{ordenar_por}'.")
        columna = getattr(Usuario, ordenar_por)
        statement = statement.order_by(columna.desc() if sentido == "desc" else columna.asc())
    usuarios = session.exec(
        statement.offset((page - 1) * page_size).limit(page_size)
    ).all()
    items = [_serializar_usuario(session, u) for u in usuarios]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/usuarios/{usuario_id}", response_model=UsuarioRead)
def obtener_usuario(usuario_id: int, session: Session = Depends(get_session)):
    usuario = _obtener_usuario_o_404(session, usuario_id)
    return _serializar_usuario(session, usuario)


@router.post("/usuarios", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def crear_usuario(payload: UsuarioCreate, session: Session = Depends(get_session)):
    _verificar_email_unico(session, payload.email)
    usuario = Usuario(
        nombre=payload.nombre,
        email=payload.email,
        password_hash=hash_password(payload.password),
        activo=payload.activo,
    )
    session.add(usuario)
    commit_or_409(session)
    session.refresh(usuario)
    return _serializar_usuario(session, usuario)


@router.put("/usuarios/{usuario_id}", response_model=UsuarioRead)
def actualizar_usuario(
    usuario_id: int, payload: UsuarioUpdate, session: Session = Depends(get_session)
):
    usuario = _obtener_usuario_o_404(session, usuario_id)
    datos = payload.model_dump(exclude_unset=True)
    _verificar_email_unico(session, datos.get("email"), excluir_id=usuario_id)
    if datos.get("activo") is False:
        svc.validar_no_deja_sistema_sin_administrador(
            session, excluir_usuario_id=usuario_id
        )
    password = datos.pop("password", None)
    if password:
        usuario.password_hash = hash_password(password)
    for campo, valor in datos.items():
        setattr(usuario, campo, valor)
    session.add(usuario)
    commit_or_409(session)
    session.refresh(usuario)
    return _serializar_usuario(session, usuario)


@router.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(usuario_id: int, session: Session = Depends(get_session)):
    usuario = _obtener_usuario_o_404(session, usuario_id)
    session.delete(usuario)
    commit_or_409(
        session,
        mensaje="No se puede eliminar el usuario: está referenciado por otros registros.",
    )


@router.post("/usuarios/{usuario_id}/roles", response_model=UsuarioRead)
def asignar_roles_a_usuario(
    usuario_id: int, payload: AsignarRoles, session: Session = Depends(get_session)
):
    usuario = _obtener_usuario_o_404(session, usuario_id)
    for rol_id in payload.roles_ids:
        _obtener_rol_o_404(session, rol_id)
        if session.get(UsuarioRol, (usuario_id, rol_id)) is None:
            session.add(UsuarioRol(usuario_id=usuario_id, rol_id=rol_id))
    commit_or_409(session)
    return _serializar_usuario(session, usuario)


@router.delete("/usuarios/{usuario_id}/roles/{rol_id}", status_code=status.HTTP_204_NO_CONTENT)
def quitar_rol_de_usuario(
    usuario_id: int, rol_id: int, session: Session = Depends(get_session)
):
    _obtener_usuario_o_404(session, usuario_id)
    existente = session.get(UsuarioRol, (usuario_id, rol_id))
    if existente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El usuario {usuario_id} no tiene asignado el rol {rol_id}.",
        )
    svc.validar_no_deja_sistema_sin_administrador(
        session, excluir_usuario_rol=(usuario_id, rol_id)
    )
    session.delete(existente)
    commit_or_409(session)


# --- roles ---


@router.get("/roles", response_model=PaginatedResponse[RolRead])
def listar_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, description="Búsqueda por nombre"),
    session: Session = Depends(get_session),
):
    statement = select(Rol)
    if q:
        statement = statement.where(Rol.nombre.ilike(f"%{q}%"))
    total = session.exec(select(func.count()).select_from(statement.subquery())).one()
    roles = session.exec(statement.offset((page - 1) * page_size).limit(page_size)).all()
    items = [_serializar_rol(session, r) for r in roles]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/roles/{rol_id}", response_model=RolRead)
def obtener_rol(rol_id: int, session: Session = Depends(get_session)):
    rol = _obtener_rol_o_404(session, rol_id)
    return _serializar_rol(session, rol)


@router.post("/roles", response_model=RolRead, status_code=status.HTTP_201_CREATED)
def crear_rol(payload: RolCreate, session: Session = Depends(get_session)):
    _verificar_nombre_rol_unico(session, payload.nombre)
    rol = Rol(nombre=payload.nombre)
    session.add(rol)
    commit_or_409(session)
    session.refresh(rol)
    return _serializar_rol(session, rol)


@router.put("/roles/{rol_id}", response_model=RolRead)
def actualizar_rol(rol_id: int, payload: RolUpdate, session: Session = Depends(get_session)):
    rol = _obtener_rol_o_404(session, rol_id)
    datos = payload.model_dump(exclude_unset=True)
    _verificar_nombre_rol_unico(session, datos.get("nombre"), excluir_id=rol_id)
    for campo, valor in datos.items():
        setattr(rol, campo, valor)
    session.add(rol)
    commit_or_409(session)
    session.refresh(rol)
    return _serializar_rol(session, rol)


@router.delete("/roles/{rol_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_rol(rol_id: int, session: Session = Depends(get_session)):
    rol = _obtener_rol_o_404(session, rol_id)
    session.delete(rol)
    commit_or_409(
        session,
        mensaje="No se puede eliminar el rol: está referenciado por otros registros.",
    )


@router.post("/roles/{rol_id}/permisos", response_model=RolRead)
def asignar_permisos_a_rol(
    rol_id: int, payload: AsignarPermisos, session: Session = Depends(get_session)
):
    rol = _obtener_rol_o_404(session, rol_id)
    for permiso_id in payload.permisos_ids:
        permiso = session.get(Permiso, permiso_id)
        if permiso is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró el permiso con id {permiso_id}",
            )
        if session.get(RolPermiso, (rol_id, permiso_id)) is None:
            session.add(RolPermiso(rol_id=rol_id, permiso_id=permiso_id))
    commit_or_409(session)
    return _serializar_rol(session, rol)


@router.delete("/roles/{rol_id}/permisos/{permiso_id}", status_code=status.HTTP_204_NO_CONTENT)
def quitar_permiso_de_rol(
    rol_id: int, permiso_id: int, session: Session = Depends(get_session)
):
    _obtener_rol_o_404(session, rol_id)
    existente = session.get(RolPermiso, (rol_id, permiso_id))
    if existente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El rol {rol_id} no tiene asignado el permiso {permiso_id}.",
        )
    permiso = session.get(Permiso, permiso_id)
    if permiso is not None and permiso.codigo == ADMIN_PERMISO:
        svc.validar_no_deja_sistema_sin_administrador(
            session, excluir_rol_permiso=(rol_id, permiso_id)
        )
    session.delete(existente)
    commit_or_409(session)
