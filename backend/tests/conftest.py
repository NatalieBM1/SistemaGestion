"""Fixtures compartidas para pruebas de la API.

``pg_engine`` es para las pruebas que necesitan Postgres con datos reales
(reportes, comparaciones sobre las 1.000 remisiones): apunta a
TEST_DATABASE_URL, que debe ser un CLON de la base (ver NOTAS_RETOMAR.md),
nunca la base real. Sin esa variable, esas pruebas se saltan.

``client_api`` levanta la app contra una base SQLite en memoria (solo las
tablas de usuarios/roles/permisos), nunca contra la base real de
DATABASE_URL. La app se envuelve con el mismo ProxyHeadersMiddleware que
uvicorn activa con ``--proxy-headers --forwarded-allow-ips='*'`` en Render,
así las pruebas pueden simular IPs distintas con X-Forwarded-For.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.core.config import settings
from app.core.database import get_session
from app.core.rate_limit import limiter
from app.core.security import hash_password
from app.main import app
from app.models.usuario import Permiso, Rol, RolPermiso, Usuario, UsuarioRol
from app.services import email_service

PASSWORD_PRUEBA = "ClaveDePrueba123"


@pytest.fixture(scope="session")
def pg_engine():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no definida (clon de la base para pruebas).")
    if url == settings.database_url:
        pytest.fail("TEST_DATABASE_URL apunta a la base real; usa un clon.")
    engine = create_engine(url)
    yield engine
    engine.dispose()


@pytest.fixture
def engine_prueba():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tablas = [m.__table__ for m in (Usuario, Rol, Permiso, RolPermiso, UsuarioRol)]
    SQLModel.metadata.create_all(engine, tables=tablas)
    with Session(engine) as session:
        session.add(
            Usuario(
                nombre="Usuario Prueba",
                email="prueba@example.com",
                password_hash=hash_password(PASSWORD_PRUEBA),
            )
        )
        session.commit()
    yield engine
    engine.dispose()


@pytest.fixture
def correos(monkeypatch):
    """Reemplaza el envío SMTP: ninguna prueba manda correos reales. Cada
    envío queda en la lista (email, nombre, codigo)."""
    enviados: list[dict] = []
    monkeypatch.setattr(email_service, "smtp_configurado", lambda: True)
    monkeypatch.setattr(
        email_service, "enviar_codigo_recuperacion", lambda **kw: enviados.append(kw)
    )
    return enviados


@pytest.fixture
def client_api(engine_prueba, correos):
    def _session_prueba():
        with Session(engine_prueba) as session:
            yield session

    app.dependency_overrides[get_session] = _session_prueba
    limiter.reset()
    with TestClient(ProxyHeadersMiddleware(app, trusted_hosts="*")) as client:
        yield client
    limiter.reset()
    app.dependency_overrides.pop(get_session, None)
