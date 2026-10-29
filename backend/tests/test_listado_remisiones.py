"""Parte 4: el listado de remisiones sin N+1 debe dar exactamente lo mismo
que la serialización fila por fila de antes (serializar_remision), y en un
número fijo de consultas. Solo lectura sobre TEST_DATABASE_URL (clon)."""

import pytest
from sqlalchemy import event
from sqlmodel import Session

from app.models.remision import Remision
from app.routers.remisiones import listar_remisiones
from app.services import remision_service as svc

PARAMS_POR_DEFECTO = {
    "page": 1,
    "page_size": 20,
    "desde": None,
    "hasta": None,
    "numero_remision": None,
    "numero_orden_servicio": None,
    "tercero_id": None,
    "placa": None,
    "proyecto_id": None,
    "estado_facturacion": None,
    "factura": None,
    "q": None,
    "ordenar_por": None,
    "sentido": "asc",
}


def _listar(session, **kw):
    return listar_remisiones(session=session, **{**PARAMS_POR_DEFECTO, **kw})


@pytest.fixture
def session(pg_engine):
    with Session(pg_engine) as s:
        yield s


@pytest.mark.parametrize("ordenar_por", [None, "fecha", "cliente", "placa", "numero_remision", "estado"])
@pytest.mark.parametrize("sentido", ["asc", "desc"])
def test_listado_identico_a_la_serializacion_fila_por_fila(pg_engine, ordenar_por, sentido):
    # Todas las páginas (las 1.000 remisiones) con el orden por defecto; con
    # los demás órdenes, las 2 primeras (la referencia fila por fila es lenta).
    todas = ordenar_por is None
    filas = 0
    page = 1
    while todas or page <= 2:
        with Session(pg_engine) as s:
            respuesta = _listar(s, page=page, page_size=100, ordenar_por=ordenar_por, sentido=sentido)
            ids = [item.id for item in respuesta.items]
        if not ids:
            break
        # Referencia: el camino viejo, con una sesión limpia.
        with Session(pg_engine) as s:
            esperado = [svc.serializar_remision(s, s.get(Remision, i)) for i in ids]
        assert [i.model_dump(mode="json") for i in respuesta.items] == [
            e.model_dump(mode="json") for e in esperado
        ]
        filas += len(ids)
        page += 1
    if todas:
        assert filas == respuesta.total


def test_listado_hace_un_numero_fijo_de_consultas(pg_engine, session):
    consultas = []
    oyente = lambda *a, **k: consultas.append(1)
    event.listen(pg_engine, "before_cursor_execute", oyente)
    try:
        for page_size in (20, 100):
            consultas.clear()
            respuesta = _listar(session, page_size=page_size)
            assert len(respuesta.items) == page_size
            # count + página + nombres/valor total de toda la página
            assert len(consultas) == 3, (page_size, len(consultas))
    finally:
        event.remove(pg_engine, "before_cursor_execute", oyente)


def test_listado_vacio(session):
    respuesta = _listar(session, numero_remision="NO-EXISTE-XYZ")
    assert respuesta.items == [] and respuesta.total == 0
