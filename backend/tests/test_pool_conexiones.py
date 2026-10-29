"""Parte 4: pool de conexiones dentro del límite de Render free."""

from app.core.config import settings
from app.core.database import engine

MAX_CONEXIONES_RENDER_FREE = 25
WORKERS = 1  # uvicorn sin --workers (Dockerfile)
INSTANCIAS = 1  # plan free: una instancia


def test_pool_configurado_segun_settings():
    assert engine.pool.size() == settings.db_pool_size == 3
    assert engine.pool._max_overflow == settings.db_max_overflow == 7
    assert engine.pool._pre_ping is True


def test_pool_no_supera_las_conexiones_de_render_free():
    maximo = WORKERS * INSTANCIAS * (settings.db_pool_size + settings.db_max_overflow)
    assert maximo == 10
    assert maximo <= MAX_CONEXIONES_RENDER_FREE
