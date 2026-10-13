from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.deps import get_current_active_user
from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.usuario import Permiso, Rol, RolPermiso, Usuario, UsuarioRol
from app.schemas.auth import RefreshRequest, RefreshResponse, TokenResponse, UsuarioMe

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _roles_de_usuario(session: Session, usuario_id: int) -> list[str]:
    statement = (
        select(Rol.nombre)
        .join(UsuarioRol, UsuarioRol.rol_id == Rol.id)
        .where(UsuarioRol.usuario_id == usuario_id)
    )
    return list(session.exec(statement).all())


def _permisos_de_usuario(session: Session, usuario_id: int) -> list[str]:
    statement = (
        select(Permiso.codigo)
        .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
        .join(Rol, Rol.id == RolPermiso.rol_id)
        .join(UsuarioRol, UsuarioRol.rol_id == Rol.id)
        .where(UsuarioRol.usuario_id == usuario_id)
    )
    return sorted(set(session.exec(statement).all()))


def _usuario_me(session: Session, usuario: Usuario) -> UsuarioMe:
    return UsuarioMe(
        id=usuario.id,
        nombre=usuario.nombre,
        email=usuario.email,
        roles=_roles_de_usuario(session, usuario.id),
        permisos=_permisos_de_usuario(session, usuario.id),
    )


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    usuario = session.exec(
        select(Usuario).where(Usuario.email == form_data.username)
    ).first()
    if usuario is None or not verify_password(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario está inactivo",
        )

    access_token = create_access_token({"sub": str(usuario.id)})
    refresh_token = create_refresh_token({"sub": str(usuario.id)})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        usuario=_usuario_me(session, usuario),
    )


@router.post("/refresh", response_model=RefreshResponse)
def refresh(payload: RefreshRequest, session: Session = Depends(get_session)):
    try:
        data = decode_token(payload.refresh_token)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    if data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere un token de refresco, no de acceso",
        )

    usuario_id = data.get("sub")
    usuario = session.get(Usuario, int(usuario_id)) if usuario_id is not None else None
    if usuario is None or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario del token de refresco ya no es válido",
        )

    return RefreshResponse(access_token=create_access_token({"sub": str(usuario.id)}))


@router.get("/me", response_model=UsuarioMe)
def me(
    usuario: Usuario = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    return _usuario_me(session, usuario)


@router.post("/logout")
def logout(usuario: Usuario = Depends(get_current_active_user)):
    return {
        "detail": (
            "Sesión cerrada del lado del cliente. Con JWT sin estado no hay nada "
            "que invalidar en el servidor: elimine el access_token y el "
            "refresh_token donde los tenga guardados. El access_token de todas "
            "formas expira solo en 60 minutos."
        )
    }
