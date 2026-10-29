"""Parte 2: código de recuperación (hash, un uso, expiración, tope de 5
intentos), "olvidé mi contraseña" sin enumeración y token_version.
Usa la base SQLite de prueba de conftest.py."""

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.core.security import create_access_token
from app.models.usuario import Permiso, Rol, RolPermiso, Usuario, UsuarioRol
from tests.conftest import PASSWORD_PRUEBA

EMAIL = "prueba@example.com"
NUEVA = "NuevaClave456"


def _login(client, password=PASSWORD_PRUEBA, email=EMAIL):
    return client.post("/api/auth/login", data={"username": email, "password": password})


def _pedir_codigo(client, correos, email=EMAIL) -> str:
    resp = client.post("/api/auth/forgot-password", json={"email": email})
    assert resp.status_code == 200
    return correos[-1]["codigo"]


def _reset(client, codigo, password=NUEVA, email=EMAIL):
    return client.post(
        "/api/auth/reset-password",
        json={"email": email, "codigo": codigo, "nueva_password": password},
    )


def _codigo_incorrecto(codigo: str) -> str:
    return f"{(int(codigo) + 1) % 1_000_000:06d}"


def _usuario(engine) -> Usuario:
    with Session(engine) as s:
        return s.exec(select(Usuario).where(Usuario.email == EMAIL)).one()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Código de recuperación ───────────────────────────────────────────────────


def test_codigo_se_guarda_con_hash_y_es_de_un_solo_uso(client_api, correos, engine_prueba):
    codigo = _pedir_codigo(client_api, correos)
    guardado = _usuario(engine_prueba).reset_token
    assert guardado and codigo not in guardado and len(guardado) == 64

    assert _reset(client_api, codigo).status_code == 200
    assert _usuario(engine_prueba).reset_token is None
    # Reusar el mismo código falla.
    assert _reset(client_api, codigo, password="OtraMas789").status_code == 400
    assert _login(client_api, NUEVA).status_code == 200


def test_codigo_vencido_no_sirve(client_api, correos, engine_prueba):
    codigo = _pedir_codigo(client_api, correos)
    with Session(engine_prueba) as s:
        u = s.exec(select(Usuario).where(Usuario.email == EMAIL)).one()
        u.reset_token_expires = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
        s.add(u)
        s.commit()
    assert _reset(client_api, codigo).status_code == 400


def test_bloqueo_al_quinto_intento_fallido(client_api, correos, engine_prueba):
    codigo = _pedir_codigo(client_api, correos)
    malo = _codigo_incorrecto(codigo)
    for i in range(5):
        assert _reset(client_api, malo).status_code == 400
        assert _usuario(engine_prueba).reset_intentos == i + 1
    # Tras 5 fallos, ni el código correcto sirve.
    resp = _reset(client_api, codigo)
    assert resp.status_code == 400
    assert "bloqueó" in resp.json()["detail"]
    assert _login(client_api).status_code == 200  # la contraseña no cambió


def test_contador_se_reinicia_con_codigo_nuevo(client_api, correos, engine_prueba):
    codigo = _pedir_codigo(client_api, correos)
    for _ in range(5):
        _reset(client_api, _codigo_incorrecto(codigo))
    assert _usuario(engine_prueba).reset_intentos == 5

    nuevo = _pedir_codigo(client_api, correos)
    assert _usuario(engine_prueba).reset_intentos == 0
    assert _reset(client_api, nuevo).status_code == 200
    assert _usuario(engine_prueba).reset_intentos == 0


def test_contador_se_reinicia_al_usar_bien_el_codigo(client_api, correos, engine_prueba):
    codigo = _pedir_codigo(client_api, correos)
    for _ in range(3):
        _reset(client_api, _codigo_incorrecto(codigo))
    assert _reset(client_api, codigo).status_code == 200
    assert _usuario(engine_prueba).reset_intentos == 0


# ── Sin enumeración de usuarios ──────────────────────────────────────────────


def test_olvide_mi_contrasena_responde_igual_exista_o_no(client_api, correos):
    existe = client_api.post("/api/auth/forgot-password", json={"email": EMAIL})
    no_existe = client_api.post(
        "/api/auth/forgot-password", json={"email": "no-existe@example.com"}
    )
    assert existe.status_code == no_existe.status_code == 200
    assert existe.content == no_existe.content
    ignorar = {"date"}
    cab = lambda r: {k: v for k, v in r.headers.items() if k.lower() not in ignorar}
    assert cab(existe) == cab(no_existe)
    # Solo se envió correo al que existe.
    assert [c["email"] for c in correos] == [EMAIL]


def test_sin_smtp_responde_igual_exista_o_no(client_api, monkeypatch):
    from app.services import email_service

    monkeypatch.setattr(email_service, "smtp_configurado", lambda: False)
    existe = client_api.post("/api/auth/forgot-password", json={"email": EMAIL})
    no_existe = client_api.post("/api/auth/forgot-password", json={"email": "x@example.com"})
    assert existe.status_code == no_existe.status_code == 503
    assert existe.content == no_existe.content


def test_fallo_smtp_no_rompe_la_respuesta(client_api, monkeypatch, caplog):
    from app.services import email_service

    def _falla(**kw):
        raise OSError("SMTP caído")

    monkeypatch.setattr(email_service, "enviar_codigo_recuperacion", _falla)
    resp = client_api.post("/api/auth/forgot-password", json={"email": EMAIL})
    assert resp.status_code == 200
    assert "No se pudo enviar el código" in caplog.text


# ── token_version ────────────────────────────────────────────────────────────


def test_token_viejo_rechazado_tras_reset(client_api, correos):
    tokens = _login(client_api).json()
    assert client_api.get("/api/auth/me", headers=_auth(tokens["access_token"])).status_code == 200

    assert _reset(client_api, _pedir_codigo(client_api, correos)).status_code == 200

    resp = client_api.get("/api/auth/me", headers=_auth(tokens["access_token"]))
    assert resp.status_code == 401
    resp = client_api.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401

    nuevos = _login(client_api, NUEVA).json()
    assert client_api.get("/api/auth/me", headers=_auth(nuevos["access_token"])).status_code == 200
    refresco = client_api.post(
        "/api/auth/refresh", json={"refresh_token": nuevos["refresh_token"]}
    )
    assert refresco.status_code == 200
    assert (
        client_api.get("/api/auth/me", headers=_auth(refresco.json()["access_token"])).status_code
        == 200
    )


def test_token_sin_version_de_antes_del_despliegue_sigue_valiendo(client_api, engine_prueba):
    token = create_access_token({"sub": str(_usuario(engine_prueba).id)})
    assert client_api.get("/api/auth/me", headers=_auth(token)).status_code == 200


def _crear_admin(engine) -> None:
    with Session(engine) as s:
        admin = Usuario(
            nombre="Admin", email="admin@example.com", password_hash=_usuario(engine).password_hash
        )
        rol = Rol(nombre="Administrador")
        permiso = Permiso(codigo="usuarios.administrar", modulo="admin")
        s.add_all([admin, rol, permiso])
        s.flush()
        s.add_all(
            [
                RolPermiso(rol_id=rol.id, permiso_id=permiso.id),
                UsuarioRol(usuario_id=admin.id, rol_id=rol.id),
            ]
        )
        s.commit()


def test_admin_cambia_contrasena_invalida_tokens(client_api, engine_prueba):
    _crear_admin(engine_prueba)
    admin = _login(client_api, email="admin@example.com").json()["access_token"]
    victima = _login(client_api).json()["access_token"]
    uid = _usuario(engine_prueba).id

    # Cambiar solo el nombre no cierra sesiones.
    resp = client_api.put(f"/api/admin/usuarios/{uid}", json={"nombre": "Otro"}, headers=_auth(admin))
    assert resp.status_code == 200
    assert client_api.get("/api/auth/me", headers=_auth(victima)).status_code == 200

    resp = client_api.put(
        f"/api/admin/usuarios/{uid}", json={"password": "Cambiada123"}, headers=_auth(admin)
    )
    assert resp.status_code == 200
    assert client_api.get("/api/auth/me", headers=_auth(victima)).status_code == 401
    # El admin que hizo el cambio sigue con su sesión.
    assert client_api.get("/api/auth/me", headers=_auth(admin)).status_code == 200


def test_desactivar_usuario_invalida_tokens(client_api, engine_prueba):
    _crear_admin(engine_prueba)
    admin = _login(client_api, email="admin@example.com").json()["access_token"]
    victima = _login(client_api).json()
    uid = _usuario(engine_prueba).id

    resp = client_api.put(f"/api/admin/usuarios/{uid}", json={"activo": False}, headers=_auth(admin))
    assert resp.status_code == 200
    assert _usuario(engine_prueba).token_version == 1

    # Aunque lo reactiven, los tokens viejos ya no sirven.
    client_api.put(f"/api/admin/usuarios/{uid}", json={"activo": True}, headers=_auth(admin))
    assert client_api.get("/api/auth/me", headers=_auth(victima["access_token"])).status_code == 401
    resp = client_api.post("/api/auth/refresh", json={"refresh_token": victima["refresh_token"]})
    assert resp.status_code == 401
