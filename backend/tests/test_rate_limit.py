"""Límite de intentos en login y recuperación de contraseña
(app/core/rate_limit.py). Usa la base SQLite de prueba de conftest.py."""

from app.core import rate_limit
from tests.conftest import PASSWORD_PRUEBA


def _ip(ip: str) -> dict[str, str]:
    return {"X-Forwarded-For": ip}


def _login(client, email: str, password: str, ip: str):
    return client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
        headers=_ip(ip),
    )


def _assert_429(resp) -> None:
    assert resp.status_code == 429
    assert "Demasiados intentos" in resp.json()["detail"]
    assert int(resp.headers["Retry-After"]) >= 1


# ── Login: 20 por minuto por IP, 5 por minuto por correo ──────────────────────────────────────────────────────


def test_login_misma_ip_se_bloquea_al_pasar_el_limite(client_api):
    # Correos distintos para que solo actúe el límite por IP.
    for i in range(20):
        resp = _login(client_api, f"nadie{i}@example.com", "x", "203.0.113.10")
        assert resp.status_code == 401
    _assert_429(_login(client_api, "otro@example.com", "x", "203.0.113.10"))


def test_login_dos_ips_distintas_no_se_bloquean_entre_si(client_api):
    for i in range(20):
        _login(client_api, f"nadie{i}@example.com", "x", "203.0.113.10")
    _assert_429(_login(client_api, "nadie9@example.com", "x", "203.0.113.10"))

    # Otra IP (otro usuario detrás del mismo proxy de Render) sigue entrando.
    resp = _login(client_api, "prueba@example.com", PASSWORD_PRUEBA, "198.51.100.20")
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_login_mismo_correo_se_bloquea_aunque_roten_ips(client_api):
    for i in range(5):
        resp = _login(client_api, "prueba@example.com", "mala", f"192.0.2.{i + 1}")
        assert resp.status_code == 401
    # Sexta IP distinta, mismo correo: bloqueado por la clave de correo.
    _assert_429(_login(client_api, "prueba@example.com", PASSWORD_PRUEBA, "192.0.2.99"))
    # Y el correo se normaliza: mayúsculas/espacios cuentan como el mismo.
    _assert_429(_login(client_api, " PRUEBA@example.com", "mala", "192.0.2.100"))


def test_login_misma_ip_varios_usuarios_no_se_bloquea_con_6(client_api):
    # Oficina con IP compartida: 6 usuarios distintos (más que el cupo por
    # correo) entran sin bloquearse, porque por IP el cupo es 20.
    for i in range(6):
        resp = _login(client_api, f"empleado{i}@example.com", "x", "203.0.113.30")
        assert resp.status_code == 401
    resp = _login(client_api, "prueba@example.com", PASSWORD_PRUEBA, "203.0.113.30")
    assert resp.status_code == 200


def test_login_normal_sigue_funcionando(client_api):
    resp = _login(client_api, "prueba@example.com", PASSWORD_PRUEBA, "203.0.113.50")
    assert resp.status_code == 200
    assert resp.json()["usuario"]["email"] == "prueba@example.com"
    resp = _login(client_api, "prueba@example.com", "mala", "203.0.113.50")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Email o contraseña incorrectos"


def test_retry_after_refleja_la_ventana(client_api):
    for i in range(20):
        _login(client_api, f"nadie{i}@example.com", "x", "203.0.113.10")
    resp = _login(client_api, "nadie@example.com", "x", "203.0.113.10")
    _assert_429(resp)
    assert 1 <= int(resp.headers["Retry-After"]) <= 60


# ── Solicitar código: 3 por hora ─────────────────────────────────────────────


def test_solicitar_codigo_misma_ip(client_api):
    for i in range(3):
        resp = client_api.post(
            "/api/auth/forgot-password",
            json={"email": f"nadie{i}@example.com"},
            headers=_ip("203.0.113.10"),
        )
        assert resp.status_code == 200
    resp = client_api.post(
        "/api/auth/forgot-password",
        json={"email": "otro@example.com"},
        headers=_ip("203.0.113.10"),
    )
    _assert_429(resp)
    assert "minuto" in resp.json()["detail"]

    resp = client_api.post(
        "/api/auth/forgot-password",
        json={"email": "otro@example.com"},
        headers=_ip("198.51.100.20"),
    )
    assert resp.status_code == 200


def test_solicitar_codigo_mismo_correo_rotando_ips(client_api, correos):
    for i in range(3):
        resp = client_api.post(
            "/api/auth/forgot-password",
            json={"email": "prueba@example.com"},
            headers=_ip(f"192.0.2.{i + 1}"),
        )
        assert resp.status_code == 200
    resp = client_api.post(
        "/api/auth/forgot-password",
        json={"email": "prueba@example.com"},
        headers=_ip("192.0.2.99"),
    )
    _assert_429(resp)
    assert len(correos) == 3


# ── Usar código: 10 por 15 minutos ───────────────────────────────────────────


def _reset(client, email: str, ip: str):
    return client.post(
        "/api/auth/reset-password",
        json={"email": email, "codigo": "000000", "nueva_password": "OtraClave123"},
        headers=_ip(ip),
    )


def test_usar_codigo_limite_por_ip(client_api):
    for i in range(10):
        assert _reset(client_api, f"nadie{i}@example.com", "203.0.113.10").status_code == 400
    _assert_429(_reset(client_api, "nadie@example.com", "203.0.113.10"))
    assert _reset(client_api, "nadie@example.com", "198.51.100.20").status_code == 400


def test_usar_codigo_mismo_correo_rotando_ips(client_api):
    for i in range(10):
        assert _reset(client_api, "nadie@example.com", f"192.0.2.{i + 1}").status_code == 400
    _assert_429(_reset(client_api, "nadie@example.com", "192.0.2.99"))


def test_verify_reset_code_ya_no_existe(client_api):
    # Ninguna pantalla lo usaba; se eliminó en la Parte 2.
    resp = client_api.post(
        "/api/auth/verify-reset-code", json={"email": "a@b.com", "codigo": "1"}
    )
    assert resp.status_code in (404, 405)


# ── Mensaje ──────────────────────────────────────────────────────────────────


def test_describir_espera():
    assert rate_limit._describir_espera(1) == "1 segundo"
    assert rate_limit._describir_espera(45) == "45 segundos"
    assert rate_limit._describir_espera(60) == "1 minuto"
    assert rate_limit._describir_espera(61) == "2 minutos"
