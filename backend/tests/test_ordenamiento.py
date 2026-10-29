"""Bloque A: orden en servidor de las listas paginadas. Solo lectura (GET)
sobre TEST_DATABASE_URL (clon), con un usuario administrador del clon."""

import re
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.deps import get_current_active_user
from app.main import app
from app.models.ubicacion import Municipio
from app.models.usuario import Permiso, RolPermiso, Usuario, UsuarioRol

# (url, columnas ordenables) — las mismas listas blancas de cada router.
LISTAS = [
    ("/api/remisiones", ["numero_remision", "fecha", "cliente", "placa", "estado", "valor_total"]),
    ("/api/facturas", ["numero_factura", "fecha_factura", "cantidad_remisiones", "valor_total_facturado"]),
    ("/api/terceros", ["identificacion", "nombre", "telefono", "tipos", "municipio"]),
    ("/api/activos", ["placa", "tipo_activo", "clase", "bloqueado", "empresa"]),
    ("/api/admin/usuarios", ["nombre", "email", "activo", "roles"]),
    ("/api/ubicaciones/departamentos", ["nombre", "codigo_dane"]),
    ("/api/catalogos/prefijos", ["codigo", "consecutivo_actual", "es_manual"]),
    ("/api/catalogos/productos", ["codigo", "nombre"]),
]


@pytest.fixture(scope="module")
def client(pg_engine):
    with Session(pg_engine) as s:
        admin = s.exec(
            select(Usuario)
            .join(UsuarioRol, UsuarioRol.usuario_id == Usuario.id)
            .join(RolPermiso, RolPermiso.rol_id == UsuarioRol.rol_id)
            .join(Permiso, Permiso.id == RolPermiso.permiso_id)
            .where(Permiso.codigo == "usuarios.administrar", Usuario.activo.is_(True))
        ).first()
        s.expunge(admin)

    def _session():
        with Session(pg_engine) as s:
            yield s

    app.dependency_overrides[get_session] = _session
    app.dependency_overrides[get_current_active_user] = lambda: admin
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _todas_las_paginas(client, url, **params):
    items, page = [], 1
    while True:
        r = client.get(url, params={**params, "page": page, "page_size": 100})
        assert r.status_code == 200, r.text
        data = r.json()
        items += data["items"]
        if page * 100 >= data["total"]:
            return items, data["total"]
        page += 1


@pytest.mark.parametrize(("url", "columnas"), LISTAS)
def test_paginacion_estable_con_cada_orden(client, url, columnas):
    for campo in [None, *columnas]:
        for sentido in ("asc", "desc"):
            params = {"ordenar_por": campo, "sentido": sentido} if campo else {}
            items, total = _todas_las_paginas(client, url, **params)
            # Facturas no expone id: su número es único.
            ids = [i.get("id", i.get("numero_factura")) for i in items]
            assert len(ids) == total, (url, campo, sentido)
            assert len(set(ids)) == total, f"filas repetidas/perdidas: {url} {campo} {sentido}"


@pytest.mark.parametrize(("url", "_"), LISTAS)
def test_lista_blanca_rechaza_columnas_no_permitidas(client, url, _):
    for malo in ("id; DROP TABLE remisiones", "password_hash", "noexiste"):
        assert client.get(url, params={"ordenar_por": malo}).status_code == 422


def _clave_numerica(texto):
    return [int(p) if p.isdigit() else p for p in re.split(r"(\d+)", texto or "")]


def test_fecha_se_ordena_como_fecha(client):
    items, _ = _todas_las_paginas(client, "/api/remisiones", ordenar_por="fecha", sentido="asc")
    fechas = [date.fromisoformat(i["fecha"]) for i in items]
    assert fechas == sorted(fechas)


def test_numero_de_remision_por_prefijo_y_consecutivo_numerico(client):
    items, _ = _todas_las_paginas(client, "/api/remisiones", ordenar_por="numero_remision")
    claves = [(i["numero_remision"].split("-")[0], int(i["numero_remision"].split("-")[1])) for i in items]
    assert claves == sorted(claves)


def test_numero_de_factura_se_ordena_por_sus_numeros(client):
    for sentido in ("asc", "desc"):
        items, _ = _todas_las_paginas(client, "/api/facturas", ordenar_por="numero_factura", sentido=sentido)
        numeros = [i["numero_factura"] for i in items]
        assert numeros == sorted(numeros, key=_clave_numerica, reverse=sentido == "desc")


def test_valor_total_de_remisiones_como_numero(client):
    for sentido in ("asc", "desc"):
        items, _ = _todas_las_paginas(client, "/api/remisiones", ordenar_por="valor_total", sentido=sentido)
        valores = [float(i["valor_total"]) for i in items]
        assert valores == sorted(valores, reverse=sentido == "desc")


def test_columnas_calculadas_de_facturas_como_numeros(client):
    for campo in ("cantidad_remisiones", "valor_total_facturado"):
        for sentido in ("asc", "desc"):
            items, _ = _todas_las_paginas(client, "/api/facturas", ordenar_por=campo, sentido=sentido)
            valores = [float(i[campo]) for i in items]
            assert valores == sorted(valores, reverse=sentido == "desc"), (campo, sentido)


def test_identificacion_de_terceros_como_numero(client):
    items, _ = _todas_las_paginas(client, "/api/terceros", ordenar_por="identificacion")
    solo_digitos = [int(i["identificacion"]) for i in items if (i["identificacion"] or "").isdigit()]
    assert solo_digitos == sorted(solo_digitos)
    # Las que no son solo dígitos (o vacías) van al final.
    primera_no_numerica = next(
        (k for k, i in enumerate(items) if not (i["identificacion"] or "").isdigit()), len(items)
    )
    assert all(not (i["identificacion"] or "").isdigit() for i in items[primera_no_numerica:])


def test_municipios_ordenables_y_estables(client, pg_engine):
    deptos, _ = _todas_las_paginas(client, "/api/ubicaciones/departamentos")
    depto = max(deptos, key=lambda d: d["codigo_dane"] == "52")  # Nariño si existe
    url = f"/api/ubicaciones/departamentos/{depto['id']}/municipios"
    for campo in ("nombre", "codigo_dane"):
        for sentido in ("asc", "desc"):
            items, total = _todas_las_paginas(client, url, ordenar_por=campo, sentido=sentido)
            valores = [i[campo] for i in items]
            # Postgres ordena según el idioma (Ó junto a O, ignora espacios y
            # paréntesis): la referencia es el ORDER BY de la propia base.
            columna = getattr(Municipio, campo)
            with Session(pg_engine) as s:
                esperado = s.exec(
                    select(columna)
                    .where(Municipio.departamento_id == depto["id"])
                    .order_by(columna.desc() if sentido == "desc" else columna.asc(), Municipio.id)
                ).all()
            assert valores == list(esperado)
            assert len({i["id"] for i in items}) == total
