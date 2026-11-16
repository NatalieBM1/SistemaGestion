"""Cambio de la propia contraseña con sesión iniciada (POST /api/auth/cambiar-password).
Usa la base de prueba de conftest.py."""

from tests.conftest import PASSWORD_PRUEBA

EMAIL = "prueba@example.com"
NUEVA = "OtraClave789"
URL = "/api/auth/cambiar-password"


def _login(client, password=PASSWORD_PRUEBA):
    return client.post("/api/auth/login", data={"username": EMAIL, "password": password})


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _cambiar(client, token, actual=PASSWORD_PRUEBA, nueva=NUEVA):
    return client.post(URL, json={"password_actual": actual, "nueva_password": nueva}, headers=_auth(token))


def test_cambia_la_contrasena_y_la_sesion_actual_sigue(client_api):
    otra_sesion = _login(client_api).json()
    actual = _login(client_api).json()

    resp = _cambiar(client_api, actual["access_token"])
    assert resp.status_code == 200
    nuevos = resp.json()
    assert nuevos["usuario"]["email"] == EMAIL

    # La sesión desde la que se cambió sigue con los tokens nuevos.
    assert client_api.get("/api/auth/me", headers=_auth(nuevos["access_token"])).status_code == 200
    assert client_api.post("/api/auth/refresh", json={"refresh_token": nuevos["refresh_token"]}).status_code == 200

    # Las otras sesiones (y los tokens viejos) quedan cerradas.
    assert client_api.get("/api/auth/me", headers=_auth(otra_sesion["access_token"])).status_code == 401
    assert client_api.post("/api/auth/refresh", json={"refresh_token": otra_sesion["refresh_token"]}).status_code == 401

    # Solo la nueva contraseña sirve para entrar.
    assert _login(client_api).status_code == 401
    assert _login(client_api, NUEVA).status_code == 200


def test_contrasena_actual_incorrecta(client_api):
    token = _login(client_api).json()["access_token"]
    resp = _cambiar(client_api, token, actual="NoEsLaClave1")
    assert resp.status_code == 400
    assert "actual no es correcta" in resp.json()["detail"]
    assert _login(client_api).status_code == 200


def test_nueva_muy_corta_o_igual(client_api):
    token = _login(client_api).json()["access_token"]
    corta = _cambiar(client_api, token, nueva="abc123")
    assert corta.status_code == 422
    assert "8 caracteres" in corta.json()["detail"]
    igual = _cambiar(client_api, token, nueva=PASSWORD_PRUEBA)
    assert igual.status_code == 422
    assert "diferente" in igual.json()["detail"]
    assert _login(client_api).status_code == 200


def test_sin_sesion_no_se_puede(client_api):
    resp = client_api.post(URL, json={"password_actual": PASSWORD_PRUEBA, "nueva_password": NUEVA})
    assert resp.status_code == 401
