from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import Integer, case, cast
from sqlmodel import Session, func, select

from app.core.database import get_session
from app.core.deps import get_current_active_user, require_permission
from app.core.errors import commit_or_409
from app.core.ordenamiento import clausulas_orden
from app.core.uploads import leer_excel_subido
from app.models.auditoria import CargaExcel
from app.models.facturacion import Factura, RemisionFacturacion
from app.models.remision import Remision
from app.models.usuario import Usuario
from app.schemas.common import PaginatedResponse
from app.schemas.facturacion import (
    ActualizarFacturaRequest,
    ActualizarFacturaResponse,
    AgregarRemisionesFacturaRequest,
    AgregarRemisionesFacturaResponse,
    CargaExcelResponse,
    FacturarMultiplesRequest,
    FacturarMultiplesResponse,
    FacturaRead,
    FacturarRemisionRequest,
    FacturarRemisionResponse,
    RemisionFacturacionHistorialRead,
    RemisionFacturacionRead,
    ResumenFacturacionRemisionRead,
    ResumenFacturasRead,
    ResumenSeleccionRead,
)
from app.services import facturacion_excel_service as excel_svc
from app.services import facturacion_service as svc

router = APIRouter(tags=["facturacion"])


def _obtener_remision_o_404(session: Session, remision_id: int) -> Remision:
    remision = session.get(Remision, remision_id)
    if remision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró la remisión con id {remision_id}",
        )
    return remision


# --- facturación individual ---


@router.post(
    "/api/remisiones/{remision_id}/facturar",
    response_model=FacturarRemisionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("facturas.escribir"))],
)
def facturar_remision(
    remision_id: int,
    payload: FacturarRemisionRequest,
    usuario: Usuario = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    remision = _obtener_remision_o_404(session, remision_id)
    registro = svc.facturar_remision(
        session,
        remision=remision,
        numero_factura=payload.numero_factura,
        fecha_factura=payload.fecha_factura,
        tipo=payload.tipo,
        valor_facturado_input=payload.valor_facturado,
        usuario_id=usuario.id,
    )
    commit_or_409(session)
    session.refresh(registro)
    session.refresh(remision)

    valor_total = svc.calcular_valor_total_remision(session, remision_id)
    valor_facturado_total = svc.calcular_valor_facturado_activo(session, remision_id)
    return FacturarRemisionResponse(
        remision_facturacion_id=registro.id,
        numero_factura=payload.numero_factura,
        tipo_facturacion=registro.tipo_facturacion,
        valor_facturado=registro.valor_facturado,
        estado_facturacion=remision.estado_facturacion,
        valor_facturado_total=valor_facturado_total,
        saldo_pendiente=valor_total - valor_facturado_total,
    )


@router.post(
    "/api/facturas/facturar-multiples/resumen",
    response_model=ResumenSeleccionRead,
    dependencies=[Depends(require_permission("facturas.escribir"))],
)
def resumen_facturar_multiples(
    remision_ids: list[int],
    session: Session = Depends(get_session),
):
    return svc.resumen_seleccion_para_facturar(session, remision_ids)


@router.post(
    "/api/facturas/facturar-multiples",
    response_model=FacturarMultiplesResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("facturas.escribir"))],
)
def facturar_multiples(
    payload: FacturarMultiplesRequest,
    usuario: Usuario = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    resultado = svc.facturar_multiples_remisiones(
        session,
        remision_ids=payload.remision_ids,
        numero_factura=payload.numero_factura,
        fecha_factura=payload.fecha_factura,
        usuario_id=usuario.id,
    )
    commit_or_409(session)
    return resultado


@router.delete(
    "/api/remisiones/{remision_id}/facturar/{remision_facturacion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("facturas.escribir"))],
)
def anular_facturacion(
    remision_id: int,
    remision_facturacion_id: int,
    usuario: Usuario = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    registro = session.get(RemisionFacturacion, remision_facturacion_id)
    if registro is None or registro.remision_id != remision_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No se encontró la facturación {remision_facturacion_id} para "
                f"la remisión {remision_id}."
            ),
        )
    svc.anular_facturacion(session, registro, usuario_id=usuario.id)
    commit_or_409(session)


@router.get(
    "/api/remisiones/{remision_id}/resumen-facturacion",
    response_model=ResumenFacturacionRemisionRead,
    dependencies=[Depends(require_permission("facturas.leer"))],
)
def obtener_resumen_facturacion(remision_id: int, session: Session = Depends(get_session)):
    remision = _obtener_remision_o_404(session, remision_id)
    valor_total = svc.calcular_valor_total_remision(session, remision_id)
    valor_facturado = svc.calcular_valor_facturado_activo(session, remision_id)
    return ResumenFacturacionRemisionRead(
        remision_id=remision_id,
        valor_total=valor_total,
        valor_facturado=valor_facturado,
        saldo_pendiente=valor_total - valor_facturado,
        estado_facturacion=remision.estado_facturacion,
    )


@router.get(
    "/api/remisiones/{remision_id}/facturaciones",
    response_model=list[RemisionFacturacionHistorialRead],
    dependencies=[Depends(require_permission("facturas.leer"))],
)
def listar_facturaciones_de_remision(remision_id: int, session: Session = Depends(get_session)):
    _obtener_remision_o_404(session, remision_id)
    return svc.listar_historial_facturacion_de_remision(session, remision_id)


# --- Excel: facturación masiva ---


@router.post(
    "/api/facturas/facturar-masivo",
    response_model=CargaExcelResponse,
    dependencies=[Depends(require_permission("facturas.escribir"))],
)
async def facturar_masivo(
    file: UploadFile = File(...),
    usuario: Usuario = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    contenido = await leer_excel_subido(file)
    filas_totales, exitosas, errores_count, detalle = excel_svc.procesar_facturar_masivo(
        session, contenido, usuario.id
    )
    session.add(
        CargaExcel(
            tipo="FACTURAR_MASIVO",
            nombre_archivo=file.filename,
            usuario_id=usuario.id,
            filas_totales=filas_totales,
            filas_exitosas=exitosas,
            filas_error=errores_count,
            detalle_errores={"errores": detalle},
        )
    )
    commit_or_409(session)
    return CargaExcelResponse(
        filas_totales=filas_totales,
        filas_exitosas=exitosas,
        filas_error=errores_count,
        detalle_errores=detalle,
    )


# --- Excel: eliminar facturación ---


@router.post(
    "/api/facturas/eliminar-por-excel",
    response_model=CargaExcelResponse,
    dependencies=[Depends(require_permission("facturas.escribir"))],
)
async def eliminar_por_excel(
    file: UploadFile = File(...),
    usuario: Usuario = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    contenido = await leer_excel_subido(file)
    filas_totales, exitosas, errores_count, detalle = excel_svc.procesar_eliminar_por_excel(
        session, contenido, usuario.id
    )
    session.add(
        CargaExcel(
            tipo="ELIMINAR_FACTURA",
            nombre_archivo=file.filename,
            usuario_id=usuario.id,
            filas_totales=filas_totales,
            filas_exitosas=exitosas,
            filas_error=errores_count,
            detalle_errores={"errores": detalle},
        )
    )
    commit_or_409(session)
    return CargaExcelResponse(
        filas_totales=filas_totales,
        filas_exitosas=exitosas,
        filas_error=errores_count,
        detalle_errores=detalle,
    )


# --- actualizar facturas ---


@router.put(
    "/api/facturas/actualizar",
    response_model=ActualizarFacturaResponse,
    dependencies=[Depends(require_permission("facturas.escribir"))],
)
def actualizar_factura(
    payload: ActualizarFacturaRequest,
    usuario: Usuario = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    factura, remisiones_ids = svc.actualizar_factura(
        session,
        numero_factura_actual=payload.numero_factura_actual,
        numero_factura_nuevo=payload.numero_factura_nuevo,
        fecha_factura_nueva=payload.fecha_factura_nueva,
        usuario_id=usuario.id,
    )
    commit_or_409(session)
    session.refresh(factura)
    return ActualizarFacturaResponse(
        numero_factura=factura.numero_factura,
        fecha_factura=factura.fecha_factura,
        remisiones_afectadas=len(remisiones_ids),
        remisiones_ids=remisiones_ids,
    )


@router.post(
    "/api/facturas/actualizar-por-excel",
    response_model=CargaExcelResponse,
    dependencies=[Depends(require_permission("facturas.escribir"))],
)
async def actualizar_por_excel(
    file: UploadFile = File(...),
    usuario: Usuario = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    contenido = await leer_excel_subido(file)
    filas_totales, exitosas, errores_count, detalle = excel_svc.procesar_actualizar_por_excel(
        session, contenido, usuario.id
    )
    session.add(
        CargaExcel(
            tipo="ACTUALIZAR_FACTURA",
            nombre_archivo=file.filename,
            usuario_id=usuario.id,
            filas_totales=filas_totales,
            filas_exitosas=exitosas,
            filas_error=errores_count,
            detalle_errores={"errores": detalle},
        )
    )
    commit_or_409(session)
    return CargaExcelResponse(
        filas_totales=filas_totales,
        filas_exitosas=exitosas,
        filas_error=errores_count,
        detalle_errores=detalle,
    )


# --- consulta ---


COLUMNAS_ORDENABLES_FACTURAS = {
    "numero_factura",
    "fecha_factura",
    "cantidad_remisiones",
    "valor_total_facturado",
}


def _parte_numerica(texto, n: int):
    parte = func.split_part(texto, "-", n)
    return case((parte.op("~")(r"^\d+$"), cast(parte, Integer)), else_=None)


def _subconsulta_activas(columna: str):
    """Mismos cálculos que serializar_factura (solo facturaciones no
    anuladas), como subconsulta para poder ordenar en el servidor."""
    rf = RemisionFacturacion
    if columna == "cantidad_remisiones":
        agregado = func.count(func.distinct(rf.remision_id))
    else:
        agregado = func.coalesce(func.sum(rf.valor_facturado), 0)
    return (
        select(agregado)
        .where(rf.factura_id == Factura.id, rf.anulada.is_(False))
        .correlate(Factura)
        .scalar_subquery()
    )


def _expresiones_numero_factura() -> list:
    """"F-7-468" se ordena por letra, luego 7 y luego 468 como números
    (como texto, F-7-1000 quedaría antes que F-7-468)."""
    numero = Factura.numero_factura
    return [func.split_part(numero, "-", 1), _parte_numerica(numero, 2), _parte_numerica(numero, 3), numero]


@router.get(
    "/api/facturas",
    response_model=PaginatedResponse[FacturaRead],
    dependencies=[Depends(require_permission("facturas.leer"))],
)
def listar_facturas(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    desde: date | None = Query(None),
    hasta: date | None = Query(None),
    numero_factura: str | None = Query(None),
    ordenar_por: str | None = Query(None),
    sentido: str = Query("asc", pattern="^(asc|desc)$"),
    session: Session = Depends(get_session),
):
    statement = select(Factura)
    if desde:
        statement = statement.where(Factura.fecha_factura >= desde)
    if hasta:
        statement = statement.where(Factura.fecha_factura <= hasta)
    if numero_factura:
        statement = statement.where(Factura.numero_factura.ilike(f"%{numero_factura}%"))

    total = session.exec(select(func.count()).select_from(statement.subquery())).one()
    if ordenar_por:
        if ordenar_por not in COLUMNAS_ORDENABLES_FACTURAS:
            raise HTTPException(status_code=422, detail=f"No se puede ordenar facturas por '{ordenar_por}'.")
        if ordenar_por == "numero_factura":
            expresiones = _expresiones_numero_factura()
        elif ordenar_por in ("cantidad_remisiones", "valor_total_facturado"):
            expresiones = [_subconsulta_activas(ordenar_por)]
        else:
            expresiones = [getattr(Factura, ordenar_por)]
        orden = clausulas_orden(expresiones, sentido, Factura.id)
    else:
        orden = [Factura.fecha_factura.desc(), Factura.id.desc()]
    facturas = session.exec(
        statement.order_by(*orden)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    items = [svc.serializar_factura(session, f) for f in facturas]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/api/facturas/resumen",
    response_model=ResumenFacturasRead,
    dependencies=[Depends(require_permission("facturas.leer"))],
)
def resumen_facturas(
    desde: date | None = Query(None),
    hasta: date | None = Query(None),
    session: Session = Depends(get_session),
):
    return svc.resumen_facturado(session, desde=desde, hasta=hasta)


@router.get(
    "/api/facturas/{numero_factura}/remisiones",
    response_model=list[RemisionFacturacionRead],
    dependencies=[Depends(require_permission("facturas.leer"))],
)
def listar_remisiones_de_factura(numero_factura: str, session: Session = Depends(get_session)):
    factura = session.exec(
        select(Factura).where(Factura.numero_factura == numero_factura)
    ).first()
    if factura is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró la factura '{numero_factura}'.",
        )
    registros = session.exec(
        select(RemisionFacturacion).where(RemisionFacturacion.factura_id == factura.id)
    ).all()
    return [svc.serializar_remision_facturacion(session, r) for r in registros]


@router.post(
    "/api/facturas/{numero_factura}/remisiones",
    response_model=AgregarRemisionesFacturaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("facturas.escribir"))],
)
def agregar_remisiones_a_factura(
    numero_factura: str,
    payload: AgregarRemisionesFacturaRequest,
    usuario: Usuario = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    resultado = svc.agregar_remisiones_a_factura(
        session,
        numero_factura=numero_factura,
        remision_ids=payload.remision_ids,
        usuario_id=usuario.id,
    )
    commit_or_409(session)
    return resultado


@router.delete(
    "/api/facturas/{numero_factura}/remisiones/{remision_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("facturas.escribir"))],
)
def quitar_remision_de_factura(
    numero_factura: str,
    remision_id: int,
    usuario: Usuario = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    svc.quitar_remision_de_factura(
        session,
        numero_factura=numero_factura,
        remision_id=remision_id,
        usuario_id=usuario.id,
    )
    commit_or_409(session)
