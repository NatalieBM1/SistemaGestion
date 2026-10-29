"""Validación de los Excel que se suben (facturación masiva, eliminar /
actualizar facturas, actualizar NIT).

Reglas: solo .xlsx, máximo 10 MB y contenido que sea de verdad un .xlsx
(un zip, firma "PK", que trae xl/workbook.xml), no solo la extensión.
"""

import io
import zipfile

from fastapi import HTTPException, UploadFile, status

MAX_MB_EXCEL = 10
MAX_BYTES_EXCEL = MAX_MB_EXCEL * 1024 * 1024
TAMANO_BLOQUE = 1024 * 1024

MENSAJE_DEMASIADO_GRANDE = (
    f"El archivo supera el tamaño máximo permitido ({MAX_MB_EXCEL} MB)."
)
MENSAJE_EXTENSION = "Solo se aceptan archivos de Excel con extensión .xlsx."
MENSAJE_CORRUPTO = (
    "El archivo no es un Excel .xlsx válido: está dañado o no es realmente "
    "un Excel (solo se le cambió la extensión). Ábrelo en Excel y guárdalo "
    "de nuevo como .xlsx."
)


async def leer_excel_subido(file: UploadFile) -> bytes:
    """Devuelve el contenido del archivo o lanza 415 / 413 / 422.

    Lee por bloques y corta apenas pasa el máximo, así un archivo enorme no
    llega a cargarse entero en memoria.
    """
    if not (file.filename or "").lower().endswith(".xlsx"):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, MENSAJE_EXTENSION)

    partes: list[bytes] = []
    leidos = 0
    while bloque := await file.read(TAMANO_BLOQUE):
        leidos += len(bloque)
        if leidos > MAX_BYTES_EXCEL:
            raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, MENSAJE_DEMASIADO_GRANDE)
        partes.append(bloque)
    contenido = b"".join(partes)

    if not contenido.startswith(b"PK\x03\x04"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, MENSAJE_CORRUPTO)
    try:
        with zipfile.ZipFile(io.BytesIO(contenido)) as zf:
            if "xl/workbook.xml" not in zf.namelist() or zf.testzip() is not None:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, MENSAJE_CORRUPTO)
    except zipfile.BadZipFile as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, MENSAJE_CORRUPTO) from exc
    return contenido
