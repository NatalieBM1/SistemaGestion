from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.core.database import get_session
from app.core.deps import require_permission
from app.services import reportes_service as svc

router = APIRouter(prefix="/api/reportes", tags=["reportes"])

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get(
    "/remisiones-general",
    dependencies=[Depends(require_permission("remisiones.leer"))],
)
def reporte_remisiones_general(
    desde: date | None = Query(None),
    hasta: date | None = Query(None),
    cliente_id: int | None = Query(None),
    proyecto_id: int | None = Query(None),
    vehiculo_id: int | None = Query(None),
    camabaja_id: int | None = Query(None),
    estado_facturacion: str | None = Query(None),
    session: Session = Depends(get_session),
):
    buffer = svc.generar_reporte_general(
        session,
        desde=desde,
        hasta=hasta,
        cliente_id=cliente_id,
        proyecto_id=proyecto_id,
        vehiculo_id=vehiculo_id,
        camabaja_id=camabaja_id,
        estado_facturacion=estado_facturacion,
    )
    return StreamingResponse(
        buffer,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": "attachment; filename=reporte_remisiones_general.xlsx"},
    )


@router.get(
    "/remisiones-facturadas",
    dependencies=[Depends(require_permission("remisiones.leer"))],
)
def reporte_remisiones_facturadas(
    desde: date | None = Query(None),
    hasta: date | None = Query(None),
    cliente_id: int | None = Query(None),
    proyecto_id: int | None = Query(None),
    vehiculo_id: int | None = Query(None),
    camabaja_id: int | None = Query(None),
    estado_facturacion: str | None = Query(None),
    session: Session = Depends(get_session),
):
    buffer = svc.generar_reporte_facturadas(
        session,
        desde=desde,
        hasta=hasta,
        cliente_id=cliente_id,
        proyecto_id=proyecto_id,
        vehiculo_id=vehiculo_id,
        camabaja_id=camabaja_id,
        estado_facturacion=estado_facturacion,
    )
    return StreamingResponse(
        buffer,
        media_type=XLSX_MEDIA_TYPE,
        headers={
            "Content-Disposition": "attachment; filename=reporte_remisiones_facturadas.xlsx"
        },
    )


@router.get(
    "/cierre-anual",
    dependencies=[Depends(require_permission("facturas.leer"))],
)
def reporte_cierre_anual(
    anio: int = Query(..., ge=2000, le=2100),
    base: str = Query("factura", pattern="^(factura|remision)$"),
    session: Session = Depends(get_session),
):
    """Excel del cierre anual: Resumen, Facturas y Detalle (32 columnas del
    reporte de facturadas). base=factura agrupa por fecha de factura (cierre
    contable); base=remision, por fecha de la remisión.

    Endpoint síncrono: FastAPI lo corre en un hilo aparte, así que generar
    un año completo no bloquea al resto de la app."""
    buffer = svc.generar_cierre_anual(session, anio=anio, base=base)
    sufijo = "" if base == "factura" else "_por_fecha_remision"
    return StreamingResponse(
        buffer,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f"attachment; filename=cierre_anual_{anio}{sufijo}.xlsx"},
    )
