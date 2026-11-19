"""Activar un usuario histórico como cuenta real (API y servicio).

Sobre el clon, dentro de una transacción que se revierte: crea un usuario
histórico FICTICIO, lo activa y verifica contraseña temporal, cambio
obligatorio, rol, auditoría y bloqueos. No deja nada guardado."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.deps import get_current_active_user
from app.core.rate_limit import limiter
from app.core.security import verify_password
from app.main import app
from app.models.auditoria import Auditoria
from app.models.usuario import Permiso, Rol, RolPermiso, Usuario, UsuarioRol
from app.services.usuarios_historicos import generar_password_temporal

CEDULA = "99000000123"


@pytest.fixture
def entorno(pg_engine):
    conexion = pg_engine.connect()
    transaccion = conexion.begin()
    s = Session(bind=conexion, join_transaction_mode="create_savepoint")
    admin = s.exec(
        select(Usuario)
        .join(UsuarioRol, UsuarioRol.usuario_id == Usuario.id)
        .join(RolPermiso, RolPermiso.rol_id == UsuarioRol.rol_id)
        .join(Permiso, Permiso.id == RolPermiso.permiso_id)
        .where(Permiso.codigo == "usuarios.administrar", Usuario.activo.is_(True))
    ).first()
    if admin is None:
        pytest.skip("El clon no tiene un administrador activo.")
    historico = Usuario(nombre="USUARIO HISTORICO FICTICIO", identificacion=CEDULA, activo=False, historico=True)
    s.add(historico)
    s.commit()

    def _sesion():
        yield s

    app.dependency_overrides[get_session] = _sesion
    app.dependency_overrides[get_current_active_user] = lambda: admin
    limiter.reset()
    try:
        with TestClient(app) as c:
            yield c, s, historico, admin
    finally:
        app.dependency_overrides.clear()
        s.close()
        transaccion.rollback()
        conexion.close()


URL = "/api/admin/usuarios/historicos/activar"


def test_contrasena_temporal_aleatoria():
    claves = {generar_password_temporal() for _ in range(50)}
    assert len(claves) == 50
    for c in claves:
        assert len(c) == 16 and any(x.isupper() for x in c) and any(x.islower() for x in c) and any(x.isdigit() for x in c)


def test_activa_el_historico_sin_duplicarlo(entorno):
    c, s, historico, admin = entorno
    antes = len(s.exec(select(Usuario.id)).all())
    r = c.post(URL, json={"identificacion": CEDULA, "email": "Ficticio.Prueba@Ejemplo.com", "rol": "Operador"})
    assert r.status_code == 200, r.text
    assert r.headers["Cache-Control"] == "no-store"
    datos = r.json()
    clave = datos["password_temporal"]
    assert len(clave) == 16
    assert datos["usuario"]["id"] == historico.id and datos["usuario"]["historico"] is False
    assert datos["usuario"]["debe_cambiar_password"] is True and datos["usuario"]["roles"] == ["Operador"]

    s.expire_all()
    u = s.get(Usuario, historico.id)
    assert len(s.exec(select(Usuario.id)).all()) == antes  # no se creó otro usuario
    assert u.email == "ficticio.prueba@ejemplo.com" and u.activo and not u.historico
    assert u.debe_cambiar_password and u.identificacion == CEDULA and u.nombre == "USUARIO HISTORICO FICTICIO"
    assert verify_password(clave, u.password_hash) and clave not in u.password_hash
    rol = s.exec(select(Rol).where(Rol.nombre == "Operador")).one()
    assert [ur.rol_id for ur in s.exec(select(UsuarioRol).where(UsuarioRol.usuario_id == u.id)).all()] == [rol.id]
    aud = s.exec(select(Auditoria).where(Auditoria.tabla == "usuarios", Auditoria.registro_id == u.id)).one()
    assert aud.accion == "ACTIVAR_HISTORICO" and aud.usuario_id == admin.id
    assert clave not in str(aud.detalle_json)

    # Ya no es histórico: una segunda activación se rechaza.
    otra = c.post(URL, json={"identificacion": CEDULA, "email": "otro@ejemplo.com", "rol": "Operador"})
    assert otra.status_code == 409


def test_errores(entorno):
    c, s, historico, admin = entorno
    assert c.post(URL, json={"identificacion": "000", "email": "a@ejemplo.com", "rol": "Operador"}).status_code == 404
    assert c.post(URL, json={"identificacion": CEDULA, "email": "no-es-correo", "rol": "Operador"}).status_code == 422
    assert c.post(URL, json={"identificacion": CEDULA, "email": "a@ejemplo.com", "rol": "Jefe"}).status_code == 422
    assert c.post(URL, json={"identificacion": CEDULA, "email": admin.email, "rol": "Operador"}).status_code == 409
    s.expire_all()
    assert s.get(Usuario, historico.id).historico  # nada cambió


def test_no_se_edita_directo_un_historico(entorno):
    c, s, historico, _admin = entorno
    r = c.put(f"/api/admin/usuarios/{historico.id}", json={"password": "CualquierCosa2026", "email": "x@ejemplo.com"})
    assert r.status_code == 409 and "Activar cuenta" in r.json()["detail"]
    rol = s.exec(select(Rol).where(Rol.nombre == "Operador")).one()
    assert c.post(f"/api/admin/usuarios/{historico.id}/roles", json={"roles_ids": [rol.id]}).status_code == 409
    # Corregir solo el nombre sí se puede.
    assert c.put(f"/api/admin/usuarios/{historico.id}", json={"nombre": "Nombre Corregido"}).status_code == 200


def test_la_cuenta_activada_debe_cambiar_la_contrasena_al_entrar(entorno):
    c, _s, _historico, _admin = entorno
    clave = c.post(URL, json={"identificacion": CEDULA, "email": "ficticio2@ejemplo.com", "rol": "Operador"}).json()["password_temporal"]
    app.dependency_overrides.pop(get_current_active_user, None)  # autenticación real
    token = c.post("/api/auth/login", data={"username": "ficticio2@ejemplo.com", "password": clave}).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    assert c.get("/api/auth/me", headers=h).json()["debe_cambiar_password"] is True
    assert c.get("/api/remisiones?page=1", headers=h).status_code == 403
    r = c.post("/api/auth/cambiar-password", json={"password_actual": clave, "nueva_password": "MiClaveNueva2026"}, headers=h)
    assert r.status_code == 200
    nuevo = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert c.get("/api/remisiones?page=1", headers=nuevo).status_code == 200
