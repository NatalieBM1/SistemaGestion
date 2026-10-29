import logging
import random
from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.deps import get_current_active_user
from app.core.fechas import ahora_utc
from app.core.rate_limit import (
    ALCANCE_USAR_CODIGO,
    LIMITE_LOGIN_CORREO,
    LIMITE_LOGIN_IP,
    LIMITE_SOLICITAR_CODIGO,
    LIMITE_USAR_CODIGO,
    limitar_por_correo,
    limiter,
)
from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    datos_token,
    decode_token,
    hash_codigo_recuperacion,
    hash_password,
    token_vigente,
    verificar_codigo_recuperacion,
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
)
from app.services import email_service
from app.core.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)


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
@limiter.limit(LIMITE_LOGIN_IP)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    limitar_por_correo(LIMITE_LOGIN_CORREO, "login", form_data.username)
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

    access_token = create_access_token(datos_token(usuario))
    refresh_token = create_refresh_token(datos_token(usuario))
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
    if usuario is None or not usuario.activo or not token_vigente(data, usuario):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario del token de refresco ya no es válido",
        )

    return RefreshResponse(access_token=create_access_token(datos_token(usuario)))


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


def _enviar_codigo_en_segundo_plano(email: str, nombre: str, codigo: str) -> None:
    """Corre después de enviar la respuesta (BackgroundTasks), así el
    tiempo de respuesta no delata si el correo existe y un SMTP lento no
    bloquea la petición. Los fallos solo quedan en el log."""
    try:
        email_service.enviar_codigo_recuperacion(email=email, nombre=nombre, codigo=codigo)
    except Exception:
        logger.exception("No se pudo enviar el código de recuperación a %s", email)


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
@limiter.limit(LIMITE_SOLICITAR_CODIGO)
def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    """Genera un código de 6 dígitos y lo envía al email del usuario.

    Responde exactamente igual (mismo código y mismo cuerpo) exista o no el
    correo, para no revelar qué correos están registrados. El correo se
    envía en segundo plano; si falla, queda en el log.
    """
    limitar_por_correo(LIMITE_SOLICITAR_CODIGO, "solicitar-codigo", payload.email)
    if not email_service.smtp_configurado():
        # Es un problema de configuración del servidor, igual para todos los
        # correos: no revela si el correo existe.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La recuperación de contraseña no está disponible en este momento.",
        )

    usuario = session.exec(
        select(Usuario).where(Usuario.email == payload.email)
    ).first()

    if usuario is not None and usuario.activo:
        codigo = f"{random.SystemRandom().randint(0, 999999):06d}"
        # UTC sin zona, igual que la columna (ver core/fechas.py).
        expira = ahora_utc() + timedelta(
            minutes=settings.reset_token_expire_minutes
        )
        # Un código nuevo reemplaza al anterior y reinicia los intentos.
        usuario.reset_token = hash_codigo_recuperacion(usuario.id, codigo)
        usuario.reset_token_expires = expira
        usuario.reset_intentos = 0
        session.add(usuario)
        session.commit()
        background_tasks.add_task(
            _enviar_codigo_en_segundo_plano, usuario.email, usuario.nombre, codigo
        )

    return {"detail": _RESET_DETAIL_GENERICO}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
@limiter.limit(LIMITE_USAR_CODIGO)
def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    session: Session = Depends(get_session),
):
    """Verifica el código y actualiza la contraseña del usuario.

    El código es de un solo uso: se borra al usarlo. Además sube
    token_version, así que cualquier sesión abierta con la contraseña
    anterior deja de valer.
    """
    limitar_por_correo(LIMITE_USAR_CODIGO, ALCANCE_USAR_CODIGO, payload.email)
    usuario = _validar_codigo_o_400(session, payload.email, payload.codigo)

    if len(payload.nueva_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La nueva contraseña debe tener al menos 8 caracteres.",
        )

    usuario.password_hash = hash_password(payload.nueva_password)
    usuario.reset_token = None
    usuario.reset_token_expires = None
    usuario.reset_intentos = 0
    usuario.token_version += 1
    session.add(usuario)
    session.commit()

    return {"detail": "Contraseña actualizada correctamente. Ya puedes iniciar sesión."}


# ── Helper interno ────────────────────────────────────────────────────────────

MAX_INTENTOS_CODIGO = 5


def _validar_codigo_o_400(session: Session, email: str, codigo: str) -> Usuario:
    """Busca el usuario, verifica el código, su expiración y los intentos.

    Cada código incorrecto suma un intento; al llegar a MAX_INTENTOS_CODIGO
    el código queda bloqueado (aunque luego se escriba bien) y hay que pedir
    uno nuevo. Devuelve el Usuario si todo es correcto; si no, HTTP 400 con
    un mensaje genérico para no dar pistas de enumeración.
    """
    _error = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            "El código es incorrecto, ya venció o se bloqueó por demasiados "
            "intentos. Si es necesario, solicita un código nuevo."
        ),
    )
    usuario = session.exec(select(Usuario).where(Usuario.email == email)).first()
    if usuario is None or not usuario.activo:
        raise _error
    if not usuario.reset_token or not usuario.reset_token_expires:
        raise _error
    if usuario.reset_intentos >= MAX_INTENTOS_CODIGO:
        raise _error

    # reset_token_expires está en UTC naive en la BD (core/fechas.py)
    if usuario.reset_token_expires < ahora_utc():
        raise _error

    if not verificar_codigo_recuperacion(usuario.id, codigo, usuario.reset_token):
        usuario.reset_intentos += 1
        session.add(usuario)
        session.commit()
        raise _error

    return usuario
