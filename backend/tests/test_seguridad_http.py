"""Parte 3: cabeceras de seguridad, /docs según entorno, CORS y validación
de los Excel subidos. Usa la base SQLite de prueba de conftest.py."""

import importlib
import io
import zipfile

import anyio
import openpyxl
import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient
from sqlmodel import Session

import app.main as main_module
from app.core.config import settings
from app.core.uploads import MAX_BYTES_EXCEL, leer_excel_subido
from app.models.usuario import Permiso, Rol, RolPermiso, Usuario, UsuarioRol
from tests.conftest import PASSWORD_PRUEBA

ORIGEN = "http://localhost:5173"
URL_SUBIDA = "/api/remisiones/actualizar-nit"


# ── Cabeceras ────────────────────────────────────────────────────────────────


def test_cabeceras_de_seguridad_en_respuestas(client_api):
    for resp in (
        client_api.get("/health"),
        client_api.post("/api/auth/login", data={"username": "x@x.com", "password": "x"}),
    ):
        assert resp.headers["x-content-type-options"] == "nosniff"
        assert resp.headers["x-frame-options"] == "DENY"
        assert resp.headers["referrer-policy"] == "no-referrer"
        assert "camera=()" in resp.headers["permissions-policy"]
        assert resp.headers["x-xss-protection"] == "0"


@pytest.fixture
def app_segun_entorno(monkeypatch):
    """Reconstruye la app con APP_ENV dado y la deja como estaba al final."""

    def _construir(entorno: str):
        monkeypatch.setattr(settings, "app_env", entorno)
        return TestClient(importlib.reload(main_module).app)

    yield _construir
    monkeypatch.undo()
    importlib.reload(main_module)


def test_desarrollo_muestra_docs_y_no_manda_hsts(app_segun_entorno):
    client = app_segun_entorno("development")
    for ruta in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(ruta).status_code == 200, ruta
    assert "strict-transport-security" not in client.get("/health").headers


def test_produccion_oculta_docs_y_manda_hsts(app_segun_entorno):
    client = app_segun_entorno("production")
    for ruta in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(ruta).status_code == 404, ruta
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers["strict-transport-security"].startswith("max-age=31536000")


def test_entorno_desconocido_cuenta_como_produccion(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "staging")
    assert settings.es_produccion


# ── CORS ─────────────────────────────────────────────────────────────────────


def _preflight(client, metodo: str, cabeceras: str):
    return client.options(
        "/api/remisiones",
        headers={
            "Origin": ORIGEN,
            "Access-Control-Request-Method": metodo,
            "Access-Control-Request-Headers": cabeceras,
        },
    )


@pytest.mark.parametrize("metodo", ["GET", "POST", "PUT", "PATCH", "DELETE"])
def test_preflight_desde_el_frontend_permitido(client_api, metodo):
    resp = _preflight(client_api, metodo, "authorization,content-type")
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == ORIGEN
    assert metodo in resp.headers["access-control-allow-methods"]
    permitidas = resp.headers["access-control-allow-headers"].lower()
    assert "authorization" in permitidas and "content-type" in permitidas


def test_preflight_rechaza_cabecera_o_metodo_no_usado(client_api):
    assert _preflight(client_api, "GET", "x-otra-cabecera").status_code == 400
    assert _preflight(client_api, "TRACE", "authorization").status_code == 400


def test_preflight_rechaza_origen_desconocido(client_api):
    resp = client_api.options(
        "/api/remisiones",
        headers={"Origin": "https://malicioso.example", "Access-Control-Request-Method": "GET"},
    )
    assert resp.status_code == 400


def test_cors_expone_retry_after(client_api):
    resp = client_api.get("/health", headers={"Origin": ORIGEN})
    assert "Retry-After" in resp.headers["access-control-expose-headers"]


# ── Subida de Excel ──────────────────────────────────────────────────────────


@pytest.fixture
def token_con_permiso_nit(client_api, engine_prueba):
    with Session(engine_prueba) as s:
        usuario = s.query(Usuario).one()
        rol = Rol(nombre="Nit")
        permiso = Permiso(codigo="remisiones.actualizar_nit", modulo="remisiones")
        s.add_all([rol, permiso])
        s.flush()
        s.add_all(
            [
                RolPermiso(rol_id=rol.id, permiso_id=permiso.id),
                UsuarioRol(usuario_id=usuario.id, rol_id=rol.id),
            ]
        )
        s.commit()
    resp = client_api.post(
        "/api/auth/login", data={"username": "prueba@example.com", "password": PASSWORD_PRUEBA}
    )
    return resp.json()["access_token"]


def _subir(client, token, nombre: str, contenido: bytes):
    return client.post(
        URL_SUBIDA,
        files={"file": (nombre, contenido, "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )


def _xlsx_valido() -> bytes:
    wb = openpyxl.Workbook()
    wb.active["A1"] = "NIT"
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def test_subida_rechaza_extension_que_no_es_xlsx(client_api, token_con_permiso_nit):
    for nombre in ("datos.csv", "datos.xls", "datos.xlsm", "datos.xlsx.exe", "sin_extension"):
        resp = _subir(client_api, token_con_permiso_nit, nombre, _xlsx_valido())
        assert resp.status_code == 415, nombre
        assert ".xlsx" in resp.json()["detail"]


def test_subida_rechaza_extension_falsa(client_api, token_con_permiso_nit):
    # Un CSV renombrado a .xlsx: la extensión engaña, la firma no.
    resp = _subir(client_api, token_con_permiso_nit, "datos.xlsx", b"nit;nombre\n123;ACME\n")
    assert resp.status_code == 422
    assert "no es un Excel .xlsx válido" in resp.json()["detail"]


def test_subida_rechaza_zip_que_no_es_excel(client_api, token_con_permiso_nit):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("hola.txt", "no soy un Excel")
    resp = _subir(client_api, token_con_permiso_nit, "datos.xlsx", buffer.getvalue())
    assert resp.status_code == 422


def test_subida_rechaza_archivo_corrupto(client_api, token_con_permiso_nit):
    valido = _xlsx_valido()
    truncado = valido[: len(valido) // 2]  # empieza con PK pero está cortado
    assert truncado.startswith(b"PK")
    resp = _subir(client_api, token_con_permiso_nit, "datos.xlsx", truncado)
    assert resp.status_code == 422


def test_subida_rechaza_archivo_apenas_mayor_a_10_mb(client_api, token_con_permiso_nit):
    # Pasa el filtro de Content-Length (está dentro del margen) y lo corta la
    # lectura por bloques.
    contenido = b"PK\x03\x04" + b"\0" * (MAX_BYTES_EXCEL - 3)
    resp = _subir(client_api, token_con_permiso_nit, "grande.xlsx", contenido)
    assert resp.status_code == 413
    assert "10 MB" in resp.json()["detail"]


def test_subida_muy_grande_se_corta_antes_de_leer_el_cuerpo(client_api):
    # Sin token: el 413 sale del middleware antes de autenticar o parsear.
    contenido = b"PK\x03\x04" + b"\0" * (MAX_BYTES_EXCEL + 200 * 1024)
    resp = client_api.post(
        URL_SUBIDA, files={"file": ("grande.xlsx", contenido)}, headers={"Origin": ORIGEN}
    )
    assert resp.status_code == 413
    assert "10 MB" in resp.json()["detail"]
    assert resp.headers["x-content-type-options"] == "nosniff"
    # Con cabecera CORS: si no, el navegador no deja leer el mensaje.
    assert resp.headers["access-control-allow-origin"] == ORIGEN


def test_xlsx_valido_pasa_la_validacion():
    contenido = _xlsx_valido()
    archivo = UploadFile(io.BytesIO(contenido), filename="Datos.XLSX")
    assert anyio.run(leer_excel_subido, archivo) == contenido
