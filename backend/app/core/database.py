from sqlmodel import Session, create_engine

from app.core.config import settings

# Pool pensado para Render free (máx. 25 conexiones a Postgres):
#   workers × instancias × (pool_size + max_overflow)
#   = 1 × 1 × (3 + 7) = 10 conexiones como máximo, dejando margen para
#   alembic/seed al arrancar, psql y conexiones de mantenimiento.
# Si se suben workers o instancias, rehacer la cuenta con
# DB_POOL_SIZE / DB_MAX_OVERFLOW (ver NOTAS_RETOMAR.md).
# pool_pre_ping descarta conexiones que Postgres cerró por inactividad.
engine = create_engine(
    settings.database_url,
    echo=False,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
)


def get_session():
    with Session(engine) as session:
        yield session
