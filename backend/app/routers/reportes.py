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
    )
    return StreamingResponse(
        buffer,
        media_type=XLSX_MEDIA_TYPE,
        headers={
            "Content-Disposition": "attachment; filename=reporte_remisiones_facturadas.xlsx"
        },
    )
