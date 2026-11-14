"""Bloque 7: orden de opciones en listas. Tipo de servicio: TRANSPORTE,
DESALOJO, MATERIA PRIMA y luego el resto alfabético; unidad de medida:
METRO CÚBICO y luego alfabético. Sin distinguir mayúsculas ni tildes.
Solo lectura (GET) sobre el clon (TEST_DATABASE_URL)."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.deps import get_current_active_user
from app.core.ordenamiento import orden_por_prioridad
from app.core.texto import normalizar
from app.main import app
from app.models.catalogos import TipoServicio
from app.models.usuario import Usuario


@pytest.fixture(scope="module")
def client(pg_engine):
    with Session(pg_engine) as s:
        admin = s.exec(select(Usuario).where(Usuario.activo.is_(True)).order_by(Usuario.id)).first()
        s.expunge(admin)

    def _session():
        with Session(pg_engine) as s:
            yield s

    app.dependency_overrides[get_session] = _session
    app.dependency_overrides[get_current_active_user] = lambda: admin
    # require_permission consulta los permisos del usuario: el primero
    # (Administrador del histórico) los tiene todos.
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _nombres(client, catalogo, **params):
    r = client.get(f"/api/catalogos/{catalogo}", params={"page_size": 100, **params})
    assert r.status_code == 200, r.text
    return [i["nombre"] for i in r.json()["items"]]


def _resto_alfabetico(nombres):
    return [normalizar(n) for n in nombres] == sorted(normalizar(n) for n in nombres)


def test_tipos_de_servicio_primero_los_tres_pedidos(client):
    nombres = _nombres(client, "tipos_servicio")
    assert [normalizar(n) for n in nombres[:3]] == ["transporte", "desalojo", "materia prima"]
    assert _resto_alfabetico(nombres[3:])


def test_unidades_de_medida_primero_metro_cubico(client):
    nombres = _nombres(client, "unidades_medida")
    assert normalizar(nombres[0]) == "metro cubico"  # en la base: "Metro cúbico"
    assert _resto_alfabetico(nombres[1:])


def test_la_prioridad_se_mantiene_al_buscar(client):
    # El formulario busca mientras se escribe: "des" trae DESALOJO antes que DESALOJOS.
    assert [normalizar(n) for n in _nombres(client, "tipos_servicio", q="des")][:2] == ["desalojo", "desalojos"]


def test_ordenar_por_columna_sigue_funcionando(client):
    # Con orden explícito por columna manda ese orden, no la prioridad.
    nombres = _nombres(client, "tipos_servicio", ordenar_por="nombre", sentido="asc")
    assert normalizar(nombres[0]) == "alquiler"
    assert normalizar(nombres[-1]) == "transporte"


def test_otros_catalogos_no_cambian(client):
    # Formas de pago no tiene prioridad: sigue por id.
    r = client.get("/api/catalogos/formas_pago", params={"page_size": 100})
    ids = [i["id"] for i in r.json()["items"]]
    assert ids == sorted(ids)


def test_sin_distinguir_mayusculas_ni_tildes(pg_engine):
    """La regla compara normalizado: "Transporte", "TRANSPORTE" o
    "transporté" caen en el mismo lugar (se prueba en SQL, sin escribir)."""
    from sqlalchemy import literal
    from sqlalchemy import select as sql_select

    with Session(pg_engine) as s:
        for variante in ("Transporte", "TRANSPORTE", "transporté", "Métro Cúbico"):
            posicion, _ = orden_por_prioridad(literal(variante), ["TRANSPORTE", "METRO CÚBICO"])
            esperado = 0 if "transp" in variante.lower() else 1
            assert s.exec(sql_select(posicion)).one()[0] == esperado, variante
        assert s.exec(select(TipoServicio)).first() is not None
