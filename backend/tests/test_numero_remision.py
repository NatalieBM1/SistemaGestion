"""Bloque 5: "GTS-6528" y "GTS-006528" son la misma remisión.
Pantalla/mensajes sin ceros, reportes con la forma de la referencia
(6 dígitos), sin cambiar lo guardado. Las pruebas con base usan el clon
(TEST_DATABASE_URL) dentro de una transacción que se revierte."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core import numero_remision as nr
from app.core.database import get_session
from app.core.deps import get_current_active_user
from app.main import app
from app.models.remision import Remision
from app.models.usuario import Permiso, RolPermiso, Usuario, UsuarioRol
from app.routers.remisiones import listar_remisiones

RUTA_REFERENCIA = nr.__file__  # solo para ubicar el repo
FILTROS_LISTADO = {
    "page": 1, "page_size": 100, "desde": None, "hasta": None, "anio": None, "mes": None, "numero_orden_servicio": None,
    "tercero_id": None, "placa": None, "proyecto_id": None, "estado_facturacion": None,
    "factura": None, "q": None, "ordenar_por": None, "sentido": "asc",
}


@pytest.mark.parametrize(
    ("entrada", "mostrar", "reporte", "clave"),
    [
        ("GTS-006528", "GTS-6528", "GTS-006528", ("GTS", 6528)),
        ("GTS-6528", "GTS-6528", "GTS-006528", ("GTS", 6528)),
        ("gts-6528", "GTS-6528", "GTS-006528", ("GTS", 6528)),
        ("GTM-29827", "GTM-29827", "GTM-029827", ("GTM", 29827)),
        ("GTM-1234567", "GTM-1234567", "GTM-1234567", ("GTM", 1234567)),
        ("PAPEL 12-A", "PAPEL 12-A", "PAPEL 12-A", None),
    ],
)
def test_formas_del_numero(entrada, mostrar, reporte, clave):
    assert nr.para_mostrar(entrada) == mostrar
    assert nr.para_reporte(entrada) == reporte
    assert nr.clave(entrada) == clave


# Los reportes escriben el número con 6 dígitos ("GTS-006525"), como las hojas
# de referencia del cliente; la regla la cubre la prueba parametrizada de arriba.


@pytest.fixture
def session_con_rollback(pg_engine):
    conexion = pg_engine.connect()
    transaccion = conexion.begin()
    session = Session(bind=conexion, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaccion.rollback()
        conexion.close()


def test_mismo_numero_con_o_sin_ceros_encuentra_la_misma(session_con_rollback):
    s = session_con_rollback
    r = s.exec(select(Remision).where(Remision.numero_remision.op("~")(r"^[A-Z]+-[1-9]\d*$"))).first()
    prefijo, n = nr.clave(r.numero_remision)
    for variante in (f"{prefijo}-{n}", f"{prefijo}-{n:06d}", f"{prefijo.lower()}-00{n}"):
        encontradas = s.exec(select(Remision).where(nr.condicion_mismo_numero(variante))).all()
        assert [x.id for x in encontradas] == [r.id], variante


@pytest.mark.parametrize("como", ["solo_numero", "sin_ceros", "con_ceros"])
def test_busqueda_acepta_las_tres_formas(pg_engine, como):
    with Session(pg_engine) as s:
        r = s.exec(select(Remision).where(Remision.numero_remision == "GTS-6520")).first()
        assert r is not None
        texto = {"solo_numero": "6520", "sin_ceros": "GTS-6520", "con_ceros": "GTS-006520"}[como]
        resultado = listar_remisiones(session=s, numero_remision=texto, **FILTROS_LISTADO)
        assert r.id in [i.id for i in resultado.items]


# El importador nuevo (app/data_import) también trata "GTS-6525" y
# "GTS-006525" como la misma remisión: ver tests/test_carga_excel.py.


@pytest.fixture
def client_clon(session_con_rollback):
    s = session_con_rollback
    admin = s.exec(
        select(Usuario)
        .join(UsuarioRol, UsuarioRol.usuario_id == Usuario.id)
        .join(RolPermiso, RolPermiso.rol_id == UsuarioRol.rol_id)
        .join(Permiso, Permiso.id == RolPermiso.permiso_id)
        .where(Permiso.codigo == "remisiones.escribir", Usuario.activo.is_(True))
    ).first()

    def _session():
        yield s

    app.dependency_overrides[get_session] = _session
    app.dependency_overrides[get_current_active_user] = lambda: admin
    try:
        with TestClient(app) as c:
            yield c, s
    finally:
        app.dependency_overrides.clear()


def test_numero_manual_con_ceros_cuenta_como_duplicado(client_clon):
    client, s = client_clon
    existente = s.exec(select(Remision).where(Remision.numero_remision.like("GTM-%"))).first()
    prefijo, n = nr.clave(existente.numero_remision)
    from app.models.catalogos import Prefijo

    gtm = s.exec(select(Prefijo).where(Prefijo.codigo == prefijo)).one()
    resp = client.post(
        "/api/remisiones",
        json={
            "prefijo_id": gtm.id,
            "numero_remision": f"{prefijo}-{n:06d}",
            "fecha": str(existente.fecha),
            "cliente_id": existente.cliente_id,
            "origen_municipio_id": existente.origen_municipio_id,
            "destino_municipio_id": existente.destino_municipio_id,
        },
    )
    assert resp.status_code == 409, resp.text
    assert resp.json()["detail"] == f"Ya existe la remisión {prefijo}-{n}."
