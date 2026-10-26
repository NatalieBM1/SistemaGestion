"""Verifica que los reportes de Remisiones salgan con el formato exacto que
pidió el cliente: mismos encabezados y mismo orden que la columna E de los
Excel de referencia en ``app/data_import/formatos/``, y que el reporte
general traiga una fila por línea de producto.

Corre contra la base configurada en DATABASE_URL (solo lectura, no escribe
nada) — pensado para correrse contra una base con datos reales o de
ensayo, no requiere una base vacía.
"""

from pathlib import Path

import openpyxl
import pytest
from sqlmodel import Session, create_engine, func, select

from app.core.config import settings
from app.models.remision import Remision, RemisionProducto
from app.services import reportes_service as svc

FORMATOS_DIR = Path(__file__).resolve().parents[1] / "app" / "data_import" / "formatos"


def _encabezados_de_referencia(nombre_archivo: str) -> list[str]:
    """Columna E (fila 7 en adelante) del Excel de referencia, tal cual —
    incluidos los errores del original (ej. "Hola salida"): el cliente
    pidió expresamente conservarlos."""
    ruta = FORMATOS_DIR / nombre_archivo
    wb = openpyxl.load_workbook(ruta, data_only=True)
    ws = wb.active
    encabezados = []
    for row in range(7, ws.max_row + 1):
        valor = ws.cell(row=row, column=5).value
        if valor is None:
            break
        encabezados.append(valor)
    return encabezados


def _encabezados_generados(buffer) -> list[str]:
    wb = openpyxl.load_workbook(buffer)
    return [celda.value for celda in wb.active[1]]


@pytest.fixture(scope="module")
def session():
    engine = create_engine(settings.database_url)
    with Session(engine) as s:
        yield s


def _assert_encabezados_identicos(generados: list[str], esperados: list[str]) -> None:
    """Compara carácter por carácter (== de strings ya lo hace) y, si
    falla, señala exactamente en qué posición y columna difiere, en vez
    de solo decir "las listas no son iguales"."""
    assert len(generados) == len(esperados), (
        f"Se esperaban {len(esperados)} columnas, se generaron {len(generados)}."
    )
    diferencias = [
        f"  columna {i + 1}: generado={g!r} vs esperado={e!r}"
        for i, (g, e) in enumerate(zip(generados, esperados))
        if g != e
    ]
    assert not diferencias, "Encabezados distintos:\n" + "\n".join(diferencias)


def test_encabezados_reporte_general(session):
    buffer = svc.generar_reporte_general(
        session,
        desde=None,
        hasta=None,
        cliente_id=None,
        proyecto_id=None,
        vehiculo_id=None,
        camabaja_id=None,
    )
    generados = _encabezados_generados(buffer)
    esperados = _encabezados_de_referencia("reporte-remisiones-general-programa_nuevo.xlsx")
    _assert_encabezados_identicos(generados, esperados)


def test_encabezados_reporte_facturadas(session):
    buffer = svc.generar_reporte_facturadas(
        session,
        desde=None,
        hasta=None,
        cliente_id=None,
        proyecto_id=None,
        vehiculo_id=None,
        camabaja_id=None,
    )
    generados = _encabezados_generados(buffer)
    esperados = _encabezados_de_referencia("reporte-remisiones-facturadas-programa_nuevo.xlsx")
    _assert_encabezados_identicos(generados, esperados)


def test_reporte_general_una_fila_por_linea_de_producto(session):
    """El reporte general trae una fila por línea de producto; una remisión
    sin ninguna línea cuenta como una sola fila (sus columnas de producto
    quedan vacías)."""
    buffer = svc.generar_reporte_general(
        session,
        desde=None,
        hasta=None,
        cliente_id=None,
        proyecto_id=None,
        vehiculo_id=None,
        camabaja_id=None,
    )
    wb = openpyxl.load_workbook(buffer)
    filas_generadas = wb.active.max_row - 1  # sin contar el encabezado

    total_lineas = session.exec(select(func.count()).select_from(RemisionProducto)).one()
    total_remisiones = session.exec(select(func.count()).select_from(Remision)).one()
    remisiones_con_lineas = session.exec(
        select(func.count(func.distinct(RemisionProducto.remision_id)))
    ).one()
    remisiones_sin_ninguna_linea = total_remisiones - remisiones_con_lineas

    assert filas_generadas == total_lineas + remisiones_sin_ninguna_linea


# --- tipo y formato de dato por columna ---
# Verifica las reglas que pidió el cliente: fechas como fecha (formato de
# celda yyyy-mm-dd), identificaciones/códigos como texto (para no perder
# ceros a la izquierda ni caer en notación científica), y valores
# monetarios como número plano. Los archivos de referencia en formatos/
# solo traen los encabezados (columna E), no datos de ejemplo en el
# formato nuevo — así que esto valida la salida propia contra las reglas
# del pedido, no contra una celda de muestra del Excel del cliente.

COLUMNAS_TEXTO_ESPERADAS = {"ID del cliente", "ID cliente", "ID del conductor"}
COLUMNAS_FECHA_ESPERADAS = {"Fecha", "Fecha de factura"}
COLUMNAS_DINERO_ESPERADAS_GENERAL = {
    "Valor Material", "Valor Flete", "Valor de comision", "Valor de costo", "Valor cama baja",
}
COLUMNAS_DINERO_ESPERADAS_FACTURADAS = {
    "Valor flete", "Valor Camabaja", "Subtotal", "Valor Material", "Total",
    "Valor facturado", "Valor pendiente",
}


def _verificar_tipos_por_columna(buffer, columnas_texto, columnas_fecha, columnas_dinero):
    import datetime
    from decimal import Decimal

    wb = openpyxl.load_workbook(buffer)
    ws = wb.active
    encabezados = [c.value for c in ws[1]]
    indice = {nombre: i + 1 for i, nombre in enumerate(encabezados)}

    for fila in ws.iter_rows(min_row=2, max_row=min(ws.max_row, 50)):
        for nombre, col in indice.items():
            celda = ws.cell(row=fila[0].row, column=col)
            if celda.value is None:
                continue  # celda vacía por falta de dato: válido, no se verifica tipo
            if nombre in columnas_texto:
                assert isinstance(celda.value, str), (
                    f"{nombre} (fila {celda.row}) debería ser texto, es {type(celda.value)}: {celda.value!r}"
                )
            elif nombre in columnas_fecha:
                assert isinstance(celda.value, (datetime.date, datetime.datetime)), (
                    f"{nombre} (fila {celda.row}) debería ser fecha, es {type(celda.value)}: {celda.value!r}"
                )
                assert "yyyy-mm-dd" in celda.number_format.lower() or celda.number_format == "yyyy-mm-dd", (
                    f"{nombre} (fila {celda.row}) tiene formato de celda {celda.number_format!r}, se esperaba yyyy-mm-dd"
                )
            elif nombre in columnas_dinero:
                assert isinstance(celda.value, (int, float, Decimal)) and not isinstance(celda.value, bool), (
                    f"{nombre} (fila {celda.row}) debería ser número, es {type(celda.value)}: {celda.value!r}"
                )


def test_tipos_de_dato_reporte_general(session):
    buffer = svc.generar_reporte_general(
        session, desde=None, hasta=None, cliente_id=None, proyecto_id=None,
        vehiculo_id=None, camabaja_id=None,
    )
    _verificar_tipos_por_columna(
        buffer, COLUMNAS_TEXTO_ESPERADAS, COLUMNAS_FECHA_ESPERADAS, COLUMNAS_DINERO_ESPERADAS_GENERAL
    )


def test_tipos_de_dato_reporte_facturadas(session):
    buffer = svc.generar_reporte_facturadas(
        session, desde=None, hasta=None, cliente_id=None, proyecto_id=None,
        vehiculo_id=None, camabaja_id=None,
    )
    _verificar_tipos_por_columna(
        buffer, COLUMNAS_TEXTO_ESPERADAS, COLUMNAS_FECHA_ESPERADAS, COLUMNAS_DINERO_ESPERADAS_FACTURADAS
    )
