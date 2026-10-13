from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

DEFAULT_MENSAJE_CONFLICTO = (
    "El registro no se pudo guardar por un conflicto de datos "
    "(posible duplicado o referencia en uso)."
)


def commit_or_409(
    session: Session, mensaje: str = DEFAULT_MENSAJE_CONFLICTO
) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=mensaje
        ) from exc


def flush_or_409(session: Session, mensaje: str = DEFAULT_MENSAJE_CONFLICTO) -> None:
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=mensaje
        ) from exc
