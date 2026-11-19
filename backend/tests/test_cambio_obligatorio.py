"""Cambio obligatorio de contraseña y usuarios iniciales de seed_auth.
Usa la base SQLite de prueba de conftest.py (no toca ninguna base real)."""

import pytest
from sqlmodel import Session, select

from app import seed_auth
from app.core.config import settings
from app.core.security import hash_password
from app.models.usuario import Rol, Usuario, UsuarioRol
from tests.conftest import PASSWORD_PRUEBA

EMAIL = "prueba@example.com"
NUEVA = "OtraClave789"


def _login(client, email=EMAIL, password=PASSWORD_PRUEBA):
    return client.post("/api/auth/login", data={"username": email, "password": password})


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _marcar(engine, email=EMAIL, valor=True):
    with Session(engine) as s:
        u = s.exec(select(Usuario).where(Usuario.email == email)).one()
        u.debe_cambiar_password = valor
        s.add(u)
        s.commit()


def _admin(engine) -> None:
    """Crea roles y permisos (seed en modo desarrollo) y un administrador."""
    with Session(engine) as s:
        seed_auth.seed(s)
        rol = s.exec(select(Rol).where(Rol.nombre == "Administrador")).one()
        admin = Usuario(nombre="ADMIN PRUEBA", email="admin@example.com", password_hash=hash_password(PASSWORD_PRUEBA))
        s.add(admin)
        s.flush()
        s.add(UsuarioRol(usuario_id=admin.id, rol_id=rol.id))
        s.commit()


def test_con_cambio_pendiente_solo_puede_ver_sesion_cambiar_o_salir(client_api, engine_prueba, monkeypatch):
    monkeypatch.setattr(settings, "app_env", "development")
    _admin(engine_prueba)
    _marcar(engine_prueba, "admin@example.com")
    token = _login(client_api, "admin@example.com").json()["access_token"]

    me = client_api.get("/api/auth/me", headers=_auth(token))
    assert me.status_code == 200 and me.json()["debe_cambiar_password"] is True

    bloqueado = client_api.get("/api/admin/usuarios", headers=_auth(token))
    assert bloqueado.status_code == 403
    assert bloqueado.json()["detail"] == "Debes cambiar tu contraseña antes de continuar."
    assert bloqueado.headers.get("X-Cambio-Password") == "obligatorio"

    assert client_api.post("/api/auth/logout", headers=_auth(token)).status_code == 200

    cambio = client_api.post(
        "/api/auth/cambiar-password",
        json={"password_actual": PASSWORD_PRUEBA, "nueva_password": NUEVA},
        headers=_auth(token),
    )
    assert cambio.status_code == 200 and cambio.json()["usuario"]["debe_cambiar_password"] is False
    nuevo = cambio.json()["access_token"]
    assert client_api.get("/api/admin/usuarios", headers=_auth(nuevo)).status_code == 200


def test_restablecer_desde_admin_activa_la_marca_salvo_para_si_mismo(client_api, engine_prueba, monkeypatch):
    monkeypatch.setattr(settings, "app_env", "development")
    _admin(engine_prueba)
    token = _login(client_api, "admin@example.com").json()["access_token"]
    with Session(engine_prueba) as s:
        otro = s.exec(select(Usuario).where(Usuario.email == EMAIL)).one().id
        yo = s.exec(select(Usuario).where(Usuario.email == "admin@example.com")).one().id

    r = client_api.put(f"/api/admin/usuarios/{otro}", json={"password": "Restablecida2026"}, headers=_auth(token))
    assert r.status_code == 200 and r.json()["debe_cambiar_password"] is True
    # Cambiar solo el nombre no activa la marca de nadie.
    r = client_api.put(f"/api/admin/usuarios/{yo}", json={"nombre": "Admin Renombrado"}, headers=_auth(token))
    assert r.json()["debe_cambiar_password"] is False
    # El administrador cambiando su propia contraseña no queda bloqueado.
    r = client_api.put(f"/api/admin/usuarios/{yo}", json={"password": "MiPropiaClave2026"}, headers=_auth(token))
    assert r.status_code == 200 and r.json()["debe_cambiar_password"] is False

    # El usuario restablecido entra, pero queda limitado hasta cambiarla.
    t2 = _login(client_api, EMAIL, "Restablecida2026").json()["access_token"]
    assert client_api.get("/api/auth/me", headers=_auth(t2)).json()["debe_cambiar_password"] is True


def test_crear_usuario_marca_solo_en_produccion(client_api, engine_prueba, monkeypatch):
    monkeypatch.setattr(settings, "app_env", "development")
    _admin(engine_prueba)
    token = _login(client_api, "admin@example.com").json()["access_token"]
    datos = {"nombre": "Nuevo", "email": "nuevo1@example.com", "password": "ClaveNueva2026"}
    assert client_api.post("/api/admin/usuarios", json=datos, headers=_auth(token)).json()["debe_cambiar_password"] is False
    monkeypatch.setattr(settings, "app_env", "production")
    datos["email"] = "nuevo2@example.com"
    assert client_api.post("/api/admin/usuarios", json=datos, headers=_auth(token)).json()["debe_cambiar_password"] is True


def test_recuperar_con_codigo_quita_la_marca(client_api, correos, engine_prueba):
    _marcar(engine_prueba)
    assert client_api.post("/api/auth/forgot-password", json={"email": EMAIL}).status_code == 200
    codigo = correos[-1]["codigo"]
    r = client_api.post("/api/auth/reset-password", json={"email": EMAIL, "codigo": codigo, "nueva_password": NUEVA})
    assert r.status_code == 200
    token = _login(client_api, EMAIL, NUEVA).json()["access_token"]
    assert client_api.get("/api/auth/me", headers=_auth(token)).json()["debe_cambiar_password"] is False


# ── seed_auth ─────────────────────────────────────────────────────────────────


def _usuarios(engine):
    with Session(engine) as s:
        return s.exec(select(Usuario)).all()


def test_seed_en_desarrollo_no_crea_usuarios(engine_prueba, monkeypatch):
    monkeypatch.setattr(settings, "app_env", "development")
    antes = len(_usuarios(engine_prueba))
    with Session(engine_prueba) as s:
        seed_auth.seed(s)
    assert len(_usuarios(engine_prueba)) == antes
    with Session(engine_prueba) as s:
        assert {r.nombre for r in s.exec(select(Rol)).all()} == {"Administrador", "Operador", "Solo Consulta"}


def test_seed_en_produccion_crea_solo_el_admin_inicial(engine_prueba, monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "admin_initial_email", None)
    monkeypatch.setattr(settings, "admin_initial_password", None)
    with Session(engine_prueba) as s, pytest.raises(SystemExit):
        seed_auth.seed(s)

    monkeypatch.setattr(settings, "admin_initial_email", "Admin.Inicial@Ejemplo.com")
    monkeypatch.setattr(settings, "admin_initial_password", "AleatoriaLarga2026xyz")
    with Session(engine_prueba) as s:
        seed_auth.seed(s)
    admin = [u for u in _usuarios(engine_prueba) if u.email == "admin.inicial@ejemplo.com"]
    assert len(admin) == 1 and admin[0].debe_cambiar_password and admin[0].activo

    # Segunda vez: ya hay un administrador activo, no crea ni cambia nada.
    total = len(_usuarios(engine_prueba))
    with Session(engine_prueba) as s:
        seed_auth.seed(s)
    assert len(_usuarios(engine_prueba)) == total
