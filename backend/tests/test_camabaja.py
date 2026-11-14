"""Bloque 3: el valor de cama baja de los productos solo existe si la
remisión tiene cama baja (camabaja_id).

Por la API real, sobre el clon (TEST_DATABASE_URL), dentro de una
transacción que se revierte al final: no queda nada escrito."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.deps import get_current_active_user
from app.core.texto import normalizar
from app.main import app
from app.models.activo import Activo
from app.models.auditoria import Auditoria
from app.models.catalogos import Producto, TipoServicio
from app.models.remision import Remision, RemisionProducto
from app.models.usuario import Permiso, RolPermiso, Usuario, UsuarioRol
from app.services.remision_service import MENSAJE_SIN_CAMABAJA


@pytest.fixture
def entorno(pg_engine):
    conexion = pg_engine.connect()
    transaccion = conexion.begin()
    session = Session(bind=conexion, join_transaction_mode="create_savepoint")
    admin = session.exec(
        select(Usuario)
        .join(UsuarioRol, UsuarioRol.usuario_id == Usuario.id)
        .join(RolPermiso, RolPermiso.rol_id == UsuarioRol.rol_id)
        .join(Permiso, Permiso.id == RolPermiso.permiso_id)
        .where(Permiso.codigo == "remisiones.escribir", Usuario.activo.is_(True))
    ).first()

    def _session():
        yield session

    app.dependency_overrides[get_session] = _session
    app.dependency_overrides[get_current_active_user] = lambda: admin
    try:
        with TestClient(app) as client:
            yield client, session
    finally:
        app.dependency_overrides.clear()
        session.close()
        transaccion.rollback()
        conexion.close()


def _tipo(session, nombre):
    return next(t for t in session.exec(select(TipoServicio)).all() if normalizar(t.nombre) == normalizar(nombre))


def _remision_editable(session, con_camabaja: bool) -> Remision:
    q = select(Remision).where(Remision.estado_facturacion == "NO_FACTURADA")
    q = q.where(Remision.camabaja_id.is_not(None) if con_camabaja else Remision.camabaja_id.is_(None))
    remision = session.exec(q.order_by(Remision.id)).first()
    if remision is None and con_camabaja:
        # Ninguna editable con cama baja en el clon: se le agrega a una.
        remision = session.exec(
            select(Remision).where(Remision.estado_facturacion == "NO_FACTURADA").order_by(Remision.id)
        ).first()
        remision.tipo_servicio_id = _tipo(session, "Cama baja").id
        remision.camabaja_id = session.exec(select(Activo.id)).first()
        session.add(remision)
        session.flush()
    return remision


def _producto_nuevo(session, valor_camabaja):
    return {
        "producto_id": session.exec(select(Producto.id)).first(),
        "cantidad": "1",
        "valor_flete": "1000",
        "valor_camabaja": valor_camabaja,
    }


def test_sin_cama_baja_se_rechaza_un_valor(entorno):
    client, session = entorno
    r = _remision_editable(session, con_camabaja=False)
    resp = client.post(f"/api/remisiones/{r.id}/productos", json=_producto_nuevo(session, "5000"))
    assert resp.status_code == 422
    assert resp.json()["detail"] == MENSAJE_SIN_CAMABAJA


@pytest.mark.parametrize("valor", ["0", "0.00", None])
def test_sin_cama_baja_vacio_o_cero_se_acepta_y_queda_en_cero(entorno, valor):
    client, session = entorno
    r = _remision_editable(session, con_camabaja=False)
    datos = _producto_nuevo(session, valor)
    if valor is None:
        datos.pop("valor_camabaja")
    resp = client.post(f"/api/remisiones/{r.id}/productos", json=datos)
    assert resp.status_code == 201, resp.text
    assert Decimal(resp.json()["producto"]["valor_camabaja"]) == 0


def test_sin_cama_baja_editar_valor_se_rechaza_y_vacio_queda_en_cero(entorno):
    client, session = entorno
    r = _remision_editable(session, con_camabaja=False)
    pid = client.post(f"/api/remisiones/{r.id}/productos", json=_producto_nuevo(session, "0")).json()["producto"]["id"]
    assert client.put(f"/api/remisiones/{r.id}/productos/{pid}", json={"valor_camabaja": "10"}).status_code == 422
    resp = client.put(f"/api/remisiones/{r.id}/productos/{pid}", json={"valor_camabaja": None})
    assert resp.status_code == 200
    assert Decimal(resp.json()["producto"]["valor_camabaja"]) == 0


def test_con_cama_baja_el_valor_se_acepta(entorno):
    client, session = entorno
    r = _remision_editable(session, con_camabaja=True)
    resp = client.post(f"/api/remisiones/{r.id}/productos", json=_producto_nuevo(session, "5000"))
    assert resp.status_code == 201, resp.text
    assert Decimal(resp.json()["producto"]["valor_camabaja"]) == 5000


def test_quitar_cama_baja_pide_confirmacion_y_limpia(entorno):
    client, session = entorno
    r = _remision_editable(session, con_camabaja=True)
    client.post(f"/api/remisiones/{r.id}/productos", json=_producto_nuevo(session, "5000"))
    otro_tipo = _tipo(session, "TRANSPORTE").id
    cambio = {"tipo_servicio_id": otro_tipo, "camabaja_id": None}

    resp = client.put(f"/api/remisiones/{r.id}", json=cambio)
    assert resp.status_code == 409
    assert "Confirma" in resp.json()["detail"]
    session.expire_all()
    assert session.get(Remision, r.id).camabaja_id is not None  # no cambió nada

    resp = client.put(f"/api/remisiones/{r.id}", json={**cambio, "limpiar_valor_camabaja": True})
    assert resp.status_code == 200, resp.text
    session.expire_all()
    assert session.get(Remision, r.id).camabaja_id is None
    valores = session.exec(select(RemisionProducto.valor_camabaja).where(RemisionProducto.remision_id == r.id)).all()
    assert all(v == 0 for v in valores)
    auditoria = session.exec(
        select(Auditoria).where(Auditoria.tabla == "remisiones", Auditoria.registro_id == r.id).order_by(Auditoria.id.desc())
    ).first()
    assert "valor_camabaja_productos" in str(auditoria.detalle_json)


def test_quitar_cama_baja_sin_valores_no_pide_confirmacion(entorno):
    client, session = entorno
    r = _remision_editable(session, con_camabaja=True)
    for p in session.exec(select(RemisionProducto).where(RemisionProducto.remision_id == r.id)).all():
        p.valor_camabaja = Decimal(0)
        session.add(p)
    session.flush()
    resp = client.put(f"/api/remisiones/{r.id}", json={"tipo_servicio_id": _tipo(session, "TRANSPORTE").id, "camabaja_id": None})
    assert resp.status_code == 200, resp.text


def test_tipo_cama_baja_en_mayusculas_sigue_reconocido(entorno):
    client, session = entorno
    tipo = _tipo(session, "Cama baja")
    tipo.nombre = "CAMA BAJA"
    session.add(tipo)
    session.flush()
    r = _remision_editable(session, con_camabaja=False)
    resp = client.put(f"/api/remisiones/{r.id}", json={"tipo_servicio_id": tipo.id, "camabaja_id": None})
    assert resp.status_code == 422
    assert "requiere" in resp.json()["detail"]


def test_historicas_coherentes_y_sin_cambios_de_valor(pg_engine):
    """Ninguna línea histórica tiene valor de cama baja en una remisión sin
    cama baja, así que la regla nueva no cambia el valor de ninguna."""
    with Session(pg_engine) as s:
        incoherentes = s.exec(
            select(RemisionProducto.id)
            .join(Remision, Remision.id == RemisionProducto.remision_id)
            .where(Remision.camabaja_id.is_(None), RemisionProducto.valor_camabaja != 0)
        ).all()
    assert incoherentes == []
