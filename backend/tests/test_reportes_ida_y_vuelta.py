"""Bloque C: ida y vuelta del reporte general con el importador existente
(app/scripts/importar_registros.py).

Dentro de UNA transacción sobre el clon (TEST_DATABASE_URL) que se revierte
al final: se toma una foto de las remisiones, se genera el reporte, se
borran remisiones/líneas/facturación, se reimporta el .xlsx generado y se
compara campo por campo con la foto. No queda nada escrito en el clon.

El reporte general no trae columnas de factura (esas van en el de
facturadas), así que la facturación no es parte de la ida y vuelta; el
estado sí (columna Estado).
"""

from decimal import Decimal

import pandas as pd
import pytest
from sqlalchemy import text
from sqlmodel import Session, select

from app.models.remision import Remision, RemisionProducto
from app.scripts import importar_registros as imp
from app.services import reportes_service as svc

FILTROS = {
    "desde": None, "hasta": None, "cliente_id": None, "proyecto_id": None,
    "vehiculo_id": None, "camabaja_id": None,
}
CAMPOS_REMISION = [
    "fecha", "forma_pago_id", "cliente_id", "conductor_id", "origen_municipio_id",
    "destino_municipio_id", "proyecto_id", "tramo_id", "tipo_servicio_id", "vehiculo_id",
    "camabaja_id", "kilometros", "hora_salida", "hora_llegada", "remision_agresur",
    "estado_facturacion", "prefijo_id", "consecutivo",
]
CAMPOS_LINEA = [
    "producto_id", "cantidad", "unidad_medida_id", "valor_material", "valor_flete",
    "valor_camabaja", "numero_viajes", "valor_comision", "valor_costo",
]


def _normalizar(valor):
    if isinstance(valor, Decimal):
        return valor.normalize()
    return valor


def _foto(session):
    foto = {}
    for r in session.exec(select(Remision)).all():
        lineas = session.exec(
            select(RemisionProducto).where(RemisionProducto.remision_id == r.id).order_by(RemisionProducto.id)
        ).all()
        foto[r.numero_remision] = {
            "campos": {c: _normalizar(getattr(r, c)) for c in CAMPOS_REMISION},
            "observaciones": r.observaciones,
            "lineas": [tuple(_normalizar(getattr(p, c)) for c in CAMPOS_LINEA) for p in lineas],
        }
    return foto


@pytest.fixture(scope="module")
def ida_y_vuelta(pg_engine, tmp_path_factory):
    carpeta = tmp_path_factory.mktemp("ida_y_vuelta")
    conexion = pg_engine.connect()
    transaccion = conexion.begin()
    session = Session(bind=conexion, join_transaction_mode="create_savepoint")
    errores_csv_original = imp.RUTA_ERRORES
    imp.RUTA_ERRORES = carpeta / "errores_importacion.csv"  # no pisar el real
    try:
        antes = _foto(session)
        archivo = carpeta / "reporte_general.xlsx"
        archivo.write_bytes(svc.generar_reporte_general(session, **FILTROS).getvalue())

        for tabla in ("remision_facturacion", "facturas", "remision_productos", "remisiones"):
            session.exec(text(f"DELETE FROM {tabla}"))
        session.flush()

        df = imp.leer_hoja_registros(ruta=archivo, hoja="Sheet1")
        no_reconocidas = imp.columnas_no_reconocidas(df)
        resultado = imp.importar_remisiones(session, imp.seleccionar_top_1000(df), dry_run=False)
        errores = (
            pd.read_csv(imp.RUTA_ERRORES).to_dict("records") if imp.RUTA_ERRORES.exists() else []
        )
        despues = _foto(session)
        yield {
            "antes": antes, "despues": despues, "resultado": resultado,
            "no_reconocidas": no_reconocidas, "errores": errores, "filas_excel": len(df),
        }
    finally:
        imp.RUTA_ERRORES = errores_csv_original
        session.close()
        transaccion.rollback()
        conexion.close()


def test_resumen(ida_y_vuelta):
    """Solo informa (pytest -s): filas leídas, creadas, errores."""
    r = ida_y_vuelta["resultado"]
    lineas = sum(len(v["lineas"]) for v in ida_y_vuelta["despues"].values())
    print(
        f"\nIDA Y VUELTA: {ida_y_vuelta['filas_excel']} filas del Excel, "
        f"{r['creadas']} remisiones reimportadas, {lineas} líneas, "
        f"{r['omitidas_por_error']} omitidas por error, errores: {ida_y_vuelta['errores']}"
    )


def test_no_hay_columnas_sin_reconocer(ida_y_vuelta):
    assert ida_y_vuelta["no_reconocidas"] == set()


def test_se_reimportan_todas_las_remisiones(ida_y_vuelta):
    r = ida_y_vuelta["resultado"]
    assert r["creadas"] == len(ida_y_vuelta["antes"]) == 1000
    assert r["omitidas_por_error"] == 0
    assert set(ida_y_vuelta["despues"]) == set(ida_y_vuelta["antes"])


def test_errores_solo_los_ya_conocidos(ida_y_vuelta):
    """El único error esperado es el que ya trae el dato original: una
    línea sin producto (GTS-6467). Ninguno por el formato del reporte."""
    motivos = {(e["numero_remision"], e["motivo"]) for e in ida_y_vuelta["errores"]}
    assert all("línea sin Producto" in m for _, m in motivos), motivos


def test_campos_de_remision_coinciden(ida_y_vuelta):
    antes, despues = ida_y_vuelta["antes"], ida_y_vuelta["despues"]
    distintas = {
        numero: {c: (antes[numero]["campos"][c], despues[numero]["campos"][c])
                 for c in CAMPOS_REMISION if antes[numero]["campos"][c] != despues[numero]["campos"][c]}
        for numero in antes
    }
    distintas = {n: d for n, d in distintas.items() if d}
    assert distintas == {}, list(distintas.items())[:5]


def test_lineas_de_producto_coinciden(ida_y_vuelta):
    antes, despues = ida_y_vuelta["antes"], ida_y_vuelta["despues"]
    distintas = [n for n in antes if antes[n]["lineas"] != despues[n]["lineas"]]
    assert distintas == [], distintas[:10]


def test_observaciones_se_conservan(ida_y_vuelta):
    # El importador agrega notas propias al final ("[Registrado
    # originalmente por: …]"); lo original tiene que seguir al principio.
    antes, despues = ida_y_vuelta["antes"], ida_y_vuelta["despues"]
    perdidas = [
        n for n in antes
        if antes[n]["observaciones"] and not (despues[n]["observaciones"] or "").startswith(antes[n]["observaciones"])
    ]
    assert perdidas == []
