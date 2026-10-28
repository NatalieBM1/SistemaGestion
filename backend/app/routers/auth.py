import random
import smtplib
from datetime import datetime, timedelta, timezone

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
    hash_password,
    verify_password,
)
from app.models.usuario import Permiso, Rol, RolPermiso, Usuario, UsuarioRol
from app.schemas.auth import (
    ForgotPasswordRequest,
    RefreshRequest,
    RefreshResponse,
    ResetPasswordRequest,
    TokenResponse,
    UsuarioMe,
    VerifyResetCodeRequest,
)
from app.services import email_service
from app.core.config import settings

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


# ── Recuperación de contraseña por código de email ───────────────────────────

_RESET_DETAIL_GENERICO = (
    "Si ese correo está registrado, recibirás un código de verificación en breve."
)


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(
    payload: ForgotPasswordRequest,
    session: Session = Depends(get_session),
):
    """Genera un código de 6 dígitos y lo envía al email del usuario.

    Siempre devuelve el mismo mensaje genérico para no revelar si el email
    existe en el sistema.
    """
    usuario = session.exec(
        select(Usuario).where(Usuario.email == payload.email)
    ).first()

    # Respondemos igual independientemente de si el usuario existe o no
    if usuario is None or not usuario.activo:
        return {"detail": _RESET_DETAIL_GENERICO}

    # Generar código numérico de 6 dígitos
    codigo = f"{random.SystemRandom().randint(0, 999999):06d}"
    expira = datetime.now(timezone.utc) + timedelta(
        minutes=settings.reset_token_expire_minutes
    )

    # Guardar hash del código (no el código en claro)
    usuario.reset_token = hash_password(codigo)
    usuario.reset_token_expires = expira
    session.add(usuario)
    session.commit()

    # Enviar el correo
    try:
        email_service.enviar_codigo_recuperacion(
            email=usuario.email,
            nombre=usuario.nombre,
            codigo=codigo,
        )
    except ValueError as exc:
        # SMTP no configurado en este entorno
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except smtplib.SMTPException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo enviar el correo. Intenta de nuevo más tarde.",
        ) from exc

    return {"detail": _RESET_DETAIL_GENERICO}


@router.post("/verify-reset-code", status_code=status.HTTP_200_OK)
def verify_reset_code(
    payload: VerifyResetCodeRequest,
    session: Session = Depends(get_session),
):
    """Verifica que el código sea correcto y no haya expirado, sin cambiar la contraseña.

    El frontend lo usa para habilitar el campo de nueva contraseña solo si el
    código es válido, evitando que el usuario escriba la contraseña nueva antes
    de confirmar el código.
    """
    _validar_codigo_o_400(session, payload.email, payload.codigo)
    return {"detail": "Código válido."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(
    payload: ResetPasswordRequest,
    session: Session = Depends(get_session),
):
    """Verifica el código y actualiza la contraseña del usuario."""
    usuario = _validar_codigo_o_400(session, payload.email, payload.codigo)

    if len(payload.nueva_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La nueva contraseña debe tener al menos 8 caracteres.",
        )

    usuario.password_hash = hash_password(payload.nueva_password)
    usuario.reset_token = None
    usuario.reset_token_expires = None
    session.add(usuario)
    session.commit()

    return {"detail": "Contraseña actualizada correctamente. Ya puedes iniciar sesión."}


# ── Helper interno ────────────────────────────────────────────────────────────

def _validar_codigo_o_400(session: Session, email: str, codigo: str) -> Usuario:
    """Busca el usuario, verifica el código y su expiración.

    Devuelve el objeto Usuario si todo es correcto; lanza HTTP 400 en cualquier
    caso de fallo (mensaje genérico para no dar pistas de enumeración).
    """
    _error = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="El código es incorrecto o ha expirado.",
    )
    usuario = session.exec(select(Usuario).where(Usuario.email == email)).first()
    if usuario is None or not usuario.activo:
        raise _error
    if not usuario.reset_token or not usuario.reset_token_expires:
        raise _error

    # Comparar expiración (reset_token_expires está en UTC naive en la BD)
    ahora = datetime.now(timezone.utc).replace(tzinfo=None)
    if usuario.reset_token_expires < ahora:
        raise _error

    if not verify_password(codigo, usuario.reset_token):
        raise _error

    return usuario
