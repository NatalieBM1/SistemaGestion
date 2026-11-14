"""Los logs no deben llevar datos personales: ni parámetros de búsqueda, ni
nombres de clientes, ni cédulas, ni correos. Solo método, plantilla de la
ruta, estado y duración. Usa la base SQLite de prueba de conftest.py."""

import logging
import re
from pathlib import Path

import pytest

from app.core.registro_peticiones import logger as logger_peticiones
from tests.conftest import PASSWORD_PRUEBA

LINEA = re.compile(r"^(GET|POST|PUT|PATCH|DELETE|OPTIONS) (/\S*) (\d{3}) \d+ms$")
SENSIBLES = ["JUAN PEREZ", "1085275375", "prueba@example.com", "q=", "?", "GTS-6520", "F-7-468"]


@pytest.fixture
def logs(caplog):
    """Captura todo: el logger de peticiones (no propaga) y la raíz."""
    caplog.set_level(logging.DEBUG)
    logger_peticiones.addHandler(caplog.handler)
    yield caplog
    logger_peticiones.removeHandler(caplog.handler)


def _lineas_peticiones(caplog):
    return [r.getMessage() for r in caplog.records if r.name == "app.peticiones"]


def _texto_servidor(caplog) -> str:
    # El logger "httpx" es el del cliente de pruebas (TestClient), no el del
    # servidor: la app no usa httpx.
    return "\n".join(r.getMessage() for r in caplog.records if not r.name.startswith("httpx"))


def test_formato_metodo_ruta_estado_duracion(client_api, logs):
    client_api.get("/health")
    (linea,) = _lineas_peticiones(logs)
    assert LINEA.match(linea), linea
    assert linea.startswith("GET /health 200 ")


def test_busqueda_no_deja_parametros_en_el_log(client_api, logs):
    client_api.get("/api/remisiones", params={"q": "JUAN PEREZ", "numero_remision": "GTS-6520"})
    client_api.get("/api/terceros", params={"q": "1085275375"})
    client_api.get("/api/facturas/F-7-468")
    lineas = _lineas_peticiones(logs)
    assert len(lineas) == 3
    assert all(LINEA.match(linea) for linea in lineas), lineas
    todo = _texto_servidor(logs)
    for sensible in SENSIBLES:
        assert sensible not in todo, sensible


def test_rutas_con_parametros_se_registran_como_plantilla(client_api, logs):
    client_api.get("/api/terceros/1085275375")
    client_api.get("/api/no-existe/1085275375")
    lineas = _lineas_peticiones(logs)
    assert lineas[0].startswith("GET /api/terceros/{tercero_id} ")
    assert lineas[1].startswith("GET /api/no-existe/{…} 404")
    assert "1085275375" not in "\n".join(lineas)


def test_login_y_recuperacion_no_registran_el_correo(client_api, logs, monkeypatch):
    from app.services import email_service

    def _falla(**kw):
        raise OSError("550 mailbox prueba@example.com unavailable")

    monkeypatch.setattr(email_service, "enviar_codigo_recuperacion", _falla)
    client_api.post("/api/auth/login", data={"username": "prueba@example.com", "password": PASSWORD_PRUEBA})
    client_api.post("/api/auth/forgot-password", json={"email": "prueba@example.com"})
    assert "No se pudo enviar el código de recuperación (usuario id=" in logs.text
    assert "prueba@example.com" not in _texto_servidor(logs)


def test_uvicorn_sin_log_de_accesos_en_el_dockerfile():
    dockerfile = (Path(__file__).resolve().parents[1] / "Dockerfile").read_text(encoding="utf-8")
    cmd = next(linea for linea in dockerfile.splitlines() if linea.startswith("CMD"))
    assert "--no-access-log" in cmd
