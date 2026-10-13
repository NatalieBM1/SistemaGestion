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
