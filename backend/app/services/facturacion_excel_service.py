"""Procesamiento de los archivos Excel del módulo de Facturación: lee y
valida el archivo, y procesa cada fila de forma independiente (una fila con
error no aborta el resto) usando SAVEPOINTs por fila para que un fallo a
mitad de fila revierta solo esa fila, no el archivo completo.
"""

import io
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.facturacion import RemisionFacturacion
from app.models.remision import Remision
from app.services import facturacion_service as svc

COLUMNAS_FACTURAR_MASIVO = ["ID", "ES_PARCIAL", "VALOR_PARCIAL", "NUMERO_FACTURA", "FECHA_FACTURA"]
COLUMNAS_ELIMINAR_POR_EXCEL = ["ID"]
COLUMNAS_ACTUALIZAR_POR_EXCEL = [
    "NUMERO_FACTURA_ACTUAL",
    "NUMERO_FACTURA_NUEVO",
    "FECHA_FACTURA_NUEVA",
]


# --- lectura y parsing ---


def leer_excel(contenido: bytes, columnas_esperadas: list[str]) -> pd.DataFrame:
    try:
        df = pd.read_excel(io.BytesIO(contenido), dtype=object)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No se pudo leer el archivo Excel: {exc}",
        ) from exc

    df = df.dropna(how="all")

    columnas_normalizadas = {str(c).strip().upper(): c for c in df.columns}
    faltantes = [c for c in columnas_esperadas if c not in columnas_normalizadas]
    if faltantes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Al archivo le faltan las columnas obligatorias: {', '.join(faltantes)}.",
        )
    # Las columnas se referencian por su nombre canónico en mayúsculas; las
    # columnas adicionales no esperadas simplemente se ignoran.
    return df.rename(columns={original: canon for canon, original in columnas_normalizadas.items()})


def _es_vacio(valor: Any) -> bool:
    if valor is None:
        return True
    if isinstance(valor, float) and pd.isna(valor):
        return True
    return bool(isinstance(valor, str) and not valor.strip())


def _parsear_fecha(valor: Any) -> date:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        try:
            return datetime.strptime(valor.strip(), "%d/%m/%Y").date()
        except ValueError:
            pass
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"'{valor}' no es una fecha válida (formato esperado dd/mm/aaaa).",
    )


def _parsear_decimal(valor: Any, campo: str) -> Decimal:
    try:
        return Decimal(str(valor).strip())
    except (InvalidOperation, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{campo} '{valor}' no es un número válido.",
        ) from exc


def _parsear_id_remision(valor: Any) -> int:
    try:
        return int(float(valor))
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"ID '{valor}' no es un id de remisión válido.",
        ) from exc


def _es_parcial_de(fila) -> str:
    valor = fila.get("ES_PARCIAL")
    return str(valor).strip().upper() if not _es_vacio(valor) else ""


# --- facturar-masivo ---


def procesar_facturar_masivo(
    session: Session, contenido: bytes, usuario_id: int | None
) -> tuple[int, int, int, list[dict]]:
    df = leer_excel(contenido, COLUMNAS_FACTURAR_MASIVO)
    filas_totales = len(df)
    errores: list[dict] = []
    bloqueados: dict[int, str] = {}

    # pre-validación a: dos filas ES_PARCIAL="N" para el mismo ID
    conteo_totales: dict[int, int] = {}
    for _, fila in df.iterrows():
        if _es_vacio(fila.get("ID")) or _es_parcial_de(fila) != "N":
            continue
        try:
            rid = _parsear_id_remision(fila.get("ID"))
        except HTTPException:
            continue
        conteo_totales[rid] = conteo_totales.get(rid, 0) + 1
    for rid, cantidad in conteo_totales.items():
        if cantidad > 1:
            bloqueados[rid] = (
                f"Hay {cantidad} filas con ES_PARCIAL='N' para el ID {rid} en el "
                "archivo; solo se permite una facturación TOTAL por remisión."
            )

    # pre-validación b: suma de VALOR_PARCIAL por ID no supera el saldo pendiente
    sumas_parciales: dict[int, Decimal] = {}
    for _, fila in df.iterrows():
        if _es_vacio(fila.get("ID")) or _es_parcial_de(fila) != "S":
            continue
        try:
            rid = _parsear_id_remision(fila.get("ID"))
            valor = _parsear_decimal(fila.get("VALOR_PARCIAL"), "VALOR_PARCIAL")
        except HTTPException:
            continue
        sumas_parciales[rid] = sumas_parciales.get(rid, Decimal(0)) + valor
    for rid, suma in sumas_parciales.items():
        if rid in bloqueados:
            continue
        remision = session.get(Remision, rid)
        if remision is None:
            continue
        valor_total = svc.calcular_valor_total_remision(session, rid)
        valor_facturado_actual = svc.calcular_valor_facturado_activo(session, rid)
        saldo = valor_total - valor_facturado_actual
        if suma > saldo:
            bloqueados[rid] = (
                f"La suma de VALOR_PARCIAL en el archivo para el ID {rid} ({suma}) "
                f"supera su saldo pendiente actual ({saldo})."
            )

    exitosas = 0
    for idx, fila in df.iterrows():
        numero_fila = int(idx) + 2
        id_reportado: Any = fila.get("ID")
        try:
            if _es_vacio(id_reportado):
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La columna ID está vacía."
                )
            remision_id = _parsear_id_remision(id_reportado)
            id_reportado = remision_id
            if remision_id in bloqueados:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=bloqueados[remision_id])

            with session.begin_nested():
                remision = session.get(Remision, remision_id)
                if remision is None:
                    raise HTTPException(
                        status.HTTP_404_NOT_FOUND,
                        detail=f"No existe la remisión con id {remision_id}.",
                    )

                es_parcial = _es_parcial_de(fila)
                if es_parcial not in ("S", "N"):
                    raise HTTPException(
                        status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"ES_PARCIAL debe ser 'S' o 'N', se recibió '{fila.get('ES_PARCIAL')}'.",
                    )
                tipo = "PARCIAL" if es_parcial == "S" else "TOTAL"

                valor_parcial = None
                if tipo == "PARCIAL":
                    if _es_vacio(fila.get("VALOR_PARCIAL")):
                        raise HTTPException(
                            status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="VALOR_PARCIAL es obligatorio cuando ES_PARCIAL='S'.",
                        )
                    valor_parcial = _parsear_decimal(fila.get("VALOR_PARCIAL"), "VALOR_PARCIAL")

                if _es_vacio(fila.get("NUMERO_FACTURA")):
                    raise HTTPException(
                        status.HTTP_422_UNPROCESSABLE_ENTITY, detail="NUMERO_FACTURA está vacío."
                    )
                numero_factura = str(fila.get("NUMERO_FACTURA")).strip()

                if _es_vacio(fila.get("FECHA_FACTURA")):
                    raise HTTPException(
                        status.HTTP_422_UNPROCESSABLE_ENTITY, detail="FECHA_FACTURA está vacía."
                    )
                fecha_factura = _parsear_fecha(fila.get("FECHA_FACTURA"))

                svc.facturar_remision(
                    session,
                    remision=remision,
                    numero_factura=numero_factura,
                    fecha_factura=fecha_factura,
                    tipo=tipo,
                    valor_facturado_input=valor_parcial,
                    usuario_id=usuario_id,
                )
            exitosas += 1
        except HTTPException as exc:
            errores.append({"fila": numero_fila, "id": id_reportado, "motivo": exc.detail})

    return filas_totales, exitosas, len(errores), errores


# --- eliminar-por-excel ---


def procesar_eliminar_por_excel(
    session: Session, contenido: bytes, usuario_id: int | None
) -> tuple[int, int, int, list[dict]]:
    df = leer_excel(contenido, COLUMNAS_ELIMINAR_POR_EXCEL)
    filas_totales = len(df)
    errores: list[dict] = []
    exitosas = 0

    for idx, fila in df.iterrows():
        numero_fila = int(idx) + 2
        id_reportado: Any = fila.get("ID")
        try:
            if _es_vacio(id_reportado):
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La columna ID está vacía."
                )
            remision_id = _parsear_id_remision(id_reportado)
            id_reportado = remision_id

            with session.begin_nested():
                remision = session.get(Remision, remision_id)
                if remision is None:
                    raise HTTPException(
                        status.HTTP_404_NOT_FOUND,
                        detail=f"No existe la remisión con id {remision_id}.",
                    )
                activos = session.exec(
                    select(RemisionFacturacion).where(
                        RemisionFacturacion.remision_id == remision_id,
                        RemisionFacturacion.anulada.is_(False),
                    )
                ).all()
                if not activos:
                    raise HTTPException(
                        status.HTTP_404_NOT_FOUND,
                        detail=f"La remisión {remision_id} no tiene facturaciones activas para anular.",
                    )
                for registro in activos:
                    svc.anular_facturacion(session, registro, usuario_id=usuario_id)
            exitosas += 1
        except HTTPException as exc:
            errores.append({"fila": numero_fila, "id": id_reportado, "motivo": exc.detail})

    return filas_totales, exitosas, len(errores), errores


# --- actualizar-por-excel ---


def procesar_actualizar_por_excel(
    session: Session, contenido: bytes, usuario_id: int | None
) -> tuple[int, int, int, list[dict]]:
    df = leer_excel(contenido, COLUMNAS_ACTUALIZAR_POR_EXCEL)
    filas_totales = len(df)
    errores: list[dict] = []
    exitosas = 0

    for idx, fila in df.iterrows():
        numero_fila = int(idx) + 2
        numero_actual_reportado: Any = fila.get("NUMERO_FACTURA_ACTUAL")
        try:
            if _es_vacio(numero_actual_reportado):
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="NUMERO_FACTURA_ACTUAL está vacío.",
                )
            numero_actual = str(numero_actual_reportado).strip()

            numero_nuevo = None
            if not _es_vacio(fila.get("NUMERO_FACTURA_NUEVO")):
                numero_nuevo = str(fila.get("NUMERO_FACTURA_NUEVO")).strip()

            fecha_nueva = None
            if not _es_vacio(fila.get("FECHA_FACTURA_NUEVA")):
                fecha_nueva = _parsear_fecha(fila.get("FECHA_FACTURA_NUEVA"))

            with session.begin_nested():
                svc.actualizar_factura(
                    session,
                    numero_factura_actual=numero_actual,
                    numero_factura_nuevo=numero_nuevo,
                    fecha_factura_nueva=fecha_nueva,
                    usuario_id=usuario_id,
                )
            exitosas += 1
        except HTTPException as exc:
            errores.append(
                {
                    "fila": numero_fila,
                    "numero_factura_actual": numero_actual_reportado,
                    "motivo": exc.detail,
                }
            )

    return filas_totales, exitosas, len(errores), errores
