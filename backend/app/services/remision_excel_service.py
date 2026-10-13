"""Procesamiento del Excel de actualización de NIT (HU-022): cambia
remisiones.cliente_id fila por fila, con SAVEPOINT por fila (mismo patrón
que Facturación) para que una fila inválida no aborte el archivo completo.
"""

import io
from typing import Any

import pandas as pd
from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.remision import Remision
from app.models.tercero import Tercero
from app.services import remision_service as svc

COLUMNAS_ACTUALIZAR_NIT = ["ID", "ID_CLIENTE"]


def _leer_excel(contenido: bytes) -> pd.DataFrame:
    try:
        df = pd.read_excel(io.BytesIO(contenido), dtype=object)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No se pudo leer el archivo Excel: {exc}",
        ) from exc

    df = df.dropna(how="all")
    columnas_normalizadas = {str(c).strip().upper(): c for c in df.columns}
    faltantes = [c for c in COLUMNAS_ACTUALIZAR_NIT if c not in columnas_normalizadas]
    if faltantes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Al archivo le faltan las columnas obligatorias: {', '.join(faltantes)}.",
        )
    return df.rename(columns={original: canon for canon, original in columnas_normalizadas.items()})


def _es_vacio(valor: Any) -> bool:
    if valor is None:
        return True
    if isinstance(valor, float) and pd.isna(valor):
        return True
    return bool(isinstance(valor, str) and not valor.strip())


def _entero(valor: Any) -> int:
    try:
        return int(float(valor))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"'{valor}' no es un id válido.",
        ) from exc


def procesar_actualizar_nit(
    session: Session, contenido: bytes, usuario_id: int | None
) -> tuple[int, int, int, list[dict]]:
    df = _leer_excel(contenido)
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
            remision_id = _entero(id_reportado)
            id_reportado = remision_id

            if _es_vacio(fila.get("ID_CLIENTE")):
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="La columna ID_CLIENTE está vacía.",
                )
            cliente_id = _entero(fila.get("ID_CLIENTE"))

            with session.begin_nested():
                remision = session.get(Remision, remision_id)
                if remision is None:
                    raise HTTPException(
                        status.HTTP_404_NOT_FOUND,
                        detail=f"No existe la remisión con id {remision_id}.",
                    )
                cliente = session.get(Tercero, cliente_id)
                if cliente is None:
                    raise HTTPException(
                        status.HTTP_404_NOT_FOUND,
                        detail=f"No existe el tercero (ID_CLIENTE) con id {cliente_id}.",
                    )
                svc.actualizar_nit_remision(session, remision, cliente_id, usuario_id)
            exitosas += 1
        except HTTPException as exc:
            errores.append({"fila": numero_fila, "id": id_reportado, "motivo": exc.detail})

    return filas_totales, exitosas, len(errores), errores
