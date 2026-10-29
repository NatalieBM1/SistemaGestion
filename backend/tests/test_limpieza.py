"""Parte 5: limpieza de bajo riesgo."""

from pathlib import Path

from sqlmodel import Session, select

from app.core.config import Settings
from app.models.usuario import Permiso, Rol, RolPermiso, Usuario, UsuarioRol
from app.routers import admin as admin_router
from app.services import admin_service
from tests.conftest import PASSWORD_PRUEBA

RAIZ = Path(__file__).resolve().parents[2]


def test_login_trae_lo_mismo_que_me(client_api, engine_prueba):
    # El frontend ya no llama a /me después de /login: tienen que coincidir.
    with Session(engine_prueba) as s:
        usuario = s.exec(select(Usuario)).one()
        rol = Rol(nombre="Operador")
        permiso = Permiso(codigo="remisiones.leer", modulo="remisiones")
        s.add_all([rol, permiso])
        s.flush()
        s.add_all(
            [
                RolPermiso(rol_id=rol.id, permiso_id=permiso.id),
                UsuarioRol(usuario_id=usuario.id, rol_id=rol.id),
            ]
        )
        s.commit()
    login = client_api.post(
        "/api/auth/login", data={"username": "prueba@example.com", "password": PASSWORD_PRUEBA}
    ).json()
    me = client_api.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {login['access_token']}"}
    ).json()
    assert login["usuario"] == me
    assert me["roles"] == ["Operador"] and me["permisos"] == ["remisiones.leer"]


def test_admin_permiso_tiene_una_sola_definicion():
    assert admin_router.ADMIN_PERMISO is admin_service.ADMIN_PERMISO
    definiciones = [
        p
        for p in (RAIZ / "backend" / "app").rglob("*.py")
        if 'ADMIN_PERMISO = "' in p.read_text(encoding="utf-8")
    ]
    assert [p.name for p in definiciones] == ["admin_service.py"]


def test_redis_url_ya_no_es_configuracion():
    assert "redis_url" not in Settings.model_fields
    assert "REDIS_URL" not in (RAIZ / ".env.example").read_text(encoding="utf-8")
