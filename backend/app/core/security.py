import hashlib
import hmac
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from passlib.context import CryptContext

from app.core.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenError(Exception):
    """El token JWT es inválido, está mal formado o expiró."""


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_codigo_recuperacion(usuario_id: int, codigo: str) -> str:
    """HMAC-SHA256 del código de recuperación, atado al usuario. Un código
    de 6 dígitos no necesita bcrypt (el límite de intentos es lo que frena
    la fuerza bruta) y así se puede comparar con hmac.compare_digest."""
    mensaje = f"reset:{usuario_id}:{codigo}".encode()
    return hmac.new(settings.secret_key.encode(), mensaje, hashlib.sha256).hexdigest()


def verificar_codigo_recuperacion(usuario_id: int, codigo: str, guardado: str) -> bool:
    return hmac.compare_digest(hash_codigo_recuperacion(usuario_id, codigo), guardado)


def datos_token(usuario) -> dict:
    """Claims comunes a access y refresh: id y versión de token."""
    return {"sub": str(usuario.id), "ver": usuario.token_version}


def token_vigente(payload: dict, usuario) -> bool:
    """El token sigue valiendo si su versión coincide con la del usuario.
    Los tokens emitidos antes de existir token_version no traen "ver" y
    cuentan como versión 0, para no cerrar todas las sesiones al desplegar."""
    return payload.get("ver", 0) == usuario.token_version


def _crear_token(data: dict, expires_delta: timedelta, token_type: str) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire, "type": token_type})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    return _crear_token(
        data,
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access",
    )


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    return _crear_token(
        data,
        expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except ExpiredSignatureError as exc:
        raise TokenError("El token ha expirado") from exc
    except JWTError as exc:
        raise TokenError("Token inválido") from exc
