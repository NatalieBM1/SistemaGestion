"""Cierre anual y filtros del listado de facturas (Bloque 4), sobre el clon.

Solo lee: verifica que las cifras del Excel del cierre coincidan con el
listado de facturas filtrado por año y con la base."""

from datetime import date
from decimal import Decimal
from io import BytesIO

import openpyxl
import pytest
from sqlmodel import Session, func, select

from app.models.facturacion import Factura, RemisionFacturacion
from app.models.remision import Remision
from app.routers.facturas import listar_facturas
from app.services import reportes_service as svc

FILTROS = {
    "page": 1, "page_size": 100, "desde": None, "hasta": None, "anio": None, "mes": None, "cliente_id": None,
    "serie": None, "estado": None, "numero_factura": None, "ordenar_por": None, "sentido": "asc",
}


@pytest.fixture
def session(pg_engine):
    with Session(pg_engine) as s:
        yield s


def _anio_con_facturas(s) -> int:
    fecha = s.exec(select(func.max(Factura.fecha_factura))).one()
    if fecha is None:
        pytest.skip("El clon no tiene facturas.")
    return fecha.year


def _todas(s, **kw):
    items, page = [], 1
    while True:
        r = listar_facturas(session=s, **{**FILTROS, **kw, "page": page})
        items += r.items
        if page * r.page_size >= r.total:
            return items, r.total
        page += 1


def test_filtro_por_anio_mes_serie_y_estado(session):
    anio = _anio_con_facturas(session)
    del_anio, total = _todas(session, anio=anio)
    assert total == len(del_anio) > 0
    assert all(f.fecha_factura.year == anio for f in del_anio)
    mes = del_anio[0].fecha_factura.month
    del_mes, _ = _todas(session, anio=anio, mes=mes)
    assert del_mes and all((f.fecha_factura.year, f.fecha_factura.month) == (anio, mes) for f in del_mes)
    serie = svc.serie_de_factura(del_anio[0].numero_factura)
    de_la_serie, _ = _todas(session, serie=serie)
    assert de_la_serie and all(svc.serie_de_factura(f.numero_factura) == serie for f in de_la_serie)
    activas, n_activas = _todas(session, estado="ACTIVA")
    _, n_anuladas = _todas(session, estado="ANULADA")
    _, n_todas = _todas(session)
    assert n_activas + n_anuladas == n_todas
    assert all(f.estado == "ACTIVA" and f.tipo in ("TOTAL", "PARCIAL") for f in activas)


def test_cierre_anual_cuadra_con_listado_y_base(session):
    anio = _anio_con_facturas(session)
    wb = openpyxl.load_workbook(BytesIO(svc.generar_cierre_anual(session, anio=anio).getvalue()), read_only=True)
    assert wb.sheetnames == ["Resumen", "Facturas", "Detalle"]
    resumen = {fila[0]: fila[1] for fila in wb["Resumen"].iter_rows(values_only=True) if fila and fila[0]}
    total = Decimal(str(resumen["Total facturado del año"]))

    esperado = session.exec(
        select(func.coalesce(func.sum(RemisionFacturacion.valor_facturado), 0))
        .join(Factura, Factura.id == RemisionFacturacion.factura_id)
        .where(
            RemisionFacturacion.anulada.is_(False),
            Factura.fecha_factura >= date(anio, 1, 1),
            Factura.fecha_factura < date(anio + 1, 1, 1),
        )
    ).one()
    assert total == Decimal(esperado)

    # Hoja Facturas = listado de facturas filtrado por el año (las activas).
    listado, _ = _todas(session, anio=anio, estado="ACTIVA")
    hoja = {fila[0]: Decimal(str(fila[5])) for fila in wb["Facturas"].iter_rows(min_row=2, values_only=True)}
    assert hoja == {f.numero_factura: Decimal(f.valor_total_facturado) for f in listado}
    assert resumen["Cantidad de facturas"] == len(listado)

    # Hoja Detalle: columnas exactas del reporte de facturadas y misma suma.
    detalle = list(wb["Detalle"].iter_rows(values_only=True))
    assert list(detalle[0]) == svc.COLUMNAS_FACTURADAS
    columna = svc.COLUMNAS_FACTURADAS.index("Valor facturado")
    assert sum(Decimal(str(f[columna])) for f in detalle[1:]) == total


def test_cierre_por_fecha_de_remision(session):
    anio = _anio_con_facturas(session)
    wb = openpyxl.load_workbook(
        BytesIO(svc.generar_cierre_anual(session, anio=anio, base="remision").getvalue()), read_only=True
    )
    resumen = {fila[0]: fila[1] for fila in wb["Resumen"].iter_rows(values_only=True) if fila and fila[0]}
    esperado = session.exec(
        select(func.coalesce(func.sum(RemisionFacturacion.valor_facturado), 0))
        .join(Remision, Remision.id == RemisionFacturacion.remision_id)
        .where(
            RemisionFacturacion.anulada.is_(False),
            Remision.fecha >= date(anio, 1, 1),
            Remision.fecha < date(anio + 1, 1, 1),
        )
    ).one()
    assert Decimal(str(resumen["Total facturado del año"])) == Decimal(esperado)
