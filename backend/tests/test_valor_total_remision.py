"""Parte 6.1: valor total de una remisión, regla única.

Decisión del cliente (2026-10-27): suma de (material + flete + camabaja) de
las líneas, SIN multiplicar por numero_viajes. La regla vive solo en
remision_service.calcular_valor_total; facturacion_service la llama y el
listado la replica en SQL (serializar_remisiones).

Antes de unificar, la versión de remisiones multiplicaba por viajes y
difería en 282 de las 1.000 remisiones; lo facturado ya coincidía con la
versión sin viajes. Solo lectura sobre TEST_DATABASE_URL (clon).
"""

import pytest
from sqlmodel import Session, select

from app.models.remision import Remision, RemisionProducto
from app.services import remision_service
from app.services.facturacion_service import (
    calcular_valor_facturado_activo,
    calcular_valor_total_remision,
)
from app.services.remision_service import calcular_valor_total


@pytest.fixture(scope="module")
def comparacion(pg_engine):
    filas = []
    with Session(pg_engine) as s:
        remisiones = s.exec(select(Remision).order_by(Remision.id)).all()
        listado = {r.id: r.valor_total for r in remision_service.serializar_remisiones(s, remisiones)}
        for r in remisiones:
            lineas = s.exec(
                select(RemisionProducto).where(RemisionProducto.remision_id == r.id)
            ).all()
            filas.append(
                {
                    "numero": r.numero_remision,
                    "estado": r.estado_facturacion,
                    "remisiones": calcular_valor_total(s, r.id),
                    "facturacion": calcular_valor_total_remision(s, r.id),
                    "listado": listado[r.id],
                    "facturado": calcular_valor_facturado_activo(s, r.id),
                    "suma_lineas": sum(
                        (p.valor_material + p.valor_flete + p.valor_camabaja for p in lineas),
                        start=0,
                    ),
                }
            )
    return filas


def test_se_comparan_las_1000_remisiones(comparacion):
    assert len(comparacion) == 1000


def test_cero_diferencias_entre_remisiones_facturacion_y_listado(comparacion):
    distintas = [
        f["numero"]
        for f in comparacion
        if not (f["remisiones"] == f["facturacion"] == f["listado"])
    ]
    assert distintas == []


def test_regla_sin_multiplicar_por_viajes(comparacion):
    assert all(f["remisiones"] == f["suma_lineas"] for f in comparacion)


def test_ninguna_facturada_queda_con_saldo_distinto_de_cero(comparacion):
    # En las FACTURADA lo facturado activo es exactamente el valor total.
    facturadas = [f for f in comparacion if f["estado"] == "FACTURADA"]
    assert facturadas
    assert [f["numero"] for f in facturadas if f["facturado"] != f["remisiones"]] == []


def test_facturacion_usa_la_funcion_unica(monkeypatch):
    from app.services import facturacion_service

    monkeypatch.setattr(facturacion_service, "calcular_valor_total", lambda s, rid: 42)
    assert facturacion_service.calcular_valor_total_remision(None, 1) == 42
