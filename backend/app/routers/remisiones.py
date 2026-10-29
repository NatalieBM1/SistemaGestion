import re
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import Integer, case, cast
from sqlmodel import Session, func, or_, select

from app.core.database import get_session
from app.core.deps import get_current_active_user, require_permission
from app.core.errors import commit_or_409, flush_or_409
from app.core.ordenamiento import clausulas_orden
from app.core.uploads import leer_excel_subido
from app.models.activo import Activo
from app.models.auditoria import CargaExcel
from app.models.catalogos import Prefijo
from app.models.facturacion import Factura, RemisionFacturacion
from app.models.orden_servicio import OrdenServicio
from app.models.remision import Remision, RemisionProducto
from app.models.tercero import Tercero
from app.models.usuario import Usuario
from app.schemas.common import PaginatedResponse
from app.schemas.facturacion import CargaExcelResponse
from app.schemas.remision import (
    CopiarRemisionRequest,
    CopiarRemisionResponse,
    RemisionCreate,
    RemisionDetalleRead,
    RemisionRead,
    RemisionUpdate,
    RemisionUpdateResponse,
)
from app.services import remision_excel_service as nit_excel_svc
from app.services import remision_service as svc

router = APIRouter(prefix="/api/remisiones", tags=["remisiones"])


# El consecutivo se guarda con ceros a la izquierda (ej. "GTS-006525"),
# pero en pantalla se muestra sin ellos (ver formatNumeroRemision en el
# frontend). Para que buscar "6525", "GTS-6525" o "GTS-006525" encuentre
# lo mismo, además del texto tal cual se busca también la versión con el
# consecutivo rellenado a 6 dígitos (el mismo ancho que usa la
# numeración automática).
_PATRON_PREFIJO_CONSECUTIVO = re.compile(r"^([A-Za-z]+)-(\d+)$")


def _patrones_busqueda_numero(texto: str) -> list[str]:
    texto = texto.strip()
    variantes = {texto}
    coincide = _PATRON_PREFIJO_CONSECUTIVO.match(texto)
    if coincide:
        prefijo, digitos = coincide.groups()
        # con ceros a la izquierda (formato que usa la numeración
        # automática, ej. "GTS-006520")...
        variantes.add(f"{prefijo}-{digitos.zfill(6)}")
        # ...y sin ellos (formato del histórico importado, ej. "GTS-6520").
        variantes.add(f"{prefijo}-{str(int(digitos))}")
    return [f"%{v}%" for v in variantes]


def _obtener_remision_o_404(session: Session, remision_id: int) -> Remision:
    remision = session.get(Remision, remision_id)
    if remision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró la remisión con id {remision_id}",
        )
    return remision


def _obtener_prefijo_o_404(session: Session, prefijo_id: int) -> Prefijo:
    prefijo = session.get(Prefijo, prefijo_id)
    if prefijo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el prefijo con id {prefijo_id}",
        )
    return prefijo


COLUMNAS_ORDENABLES_REMISIONES = {
    "numero_remision",
    "fecha",
    "cliente",
    "estado",
    "placa",
    "valor_total",
}


def _clausula_orden_remisiones(ordenar_por: str, sentido: str):
    """Lista blanca explícita (no getattr libre): cada columna ordenable
    tiene su propia expresión, porque varias no son una columna simple de
    `remisiones` (cliente/placa vienen de otra tabla, numero_remision se
    ordena por prefijo + consecutivo numérico aunque en pantalla no se
    vean los ceros)."""
    if ordenar_por not in COLUMNAS_ORDENABLES_REMISIONES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No se puede ordenar remisiones por '{ordenar_por}'.",
        )
    if ordenar_por == "valor_total":
        return clausulas_orden([svc.subconsulta_valor_total()], sentido, Remision.id)
    if ordenar_por == "fecha":
        return clausulas_orden([Remision.fecha], sentido, Remision.id)
    if ordenar_por == "estado":
        return clausulas_orden([Remision.estado_facturacion], sentido, Remision.id)
    if ordenar_por == "cliente":
        subq = select(Tercero.nombre).where(Tercero.id == Remision.cliente_id).scalar_subquery()
        return clausulas_orden([subq], sentido, Remision.id)
    if ordenar_por == "placa":
        subq = select(Activo.placa).where(Activo.id == Remision.vehiculo_id).scalar_subquery()
        return clausulas_orden([subq], sentido, Remision.id)
    # numero_remision: por prefijo (texto) y luego por consecutivo numérico.
    # El consecutivo es texto libre para prefijos manuales (puede no ser
    # dígitos) — se castea solo cuando sí lo es, para no romper el ORDER BY.
    prefijo_subq = select(Prefijo.codigo).where(Prefijo.id == Remision.prefijo_id).scalar_subquery()
    consecutivo_numerico = case(
        (Remision.consecutivo.op("~")(r"^\d+$"), cast(Remision.consecutivo, Integer)),
        else_=0,
    )
    return clausulas_orden([prefijo_subq, consecutivo_numerico, Remision.consecutivo], sentido, Remision.id)


def _remision_ids_por_factura(texto: str):
    return (
        select(RemisionFacturacion.remision_id)
        .join(Factura, Factura.id == RemisionFacturacion.factura_id)
        .where(Factura.numero_factura.ilike(f"%{texto}%"), RemisionFacturacion.anulada.is_(False))
    )


@router.get(
    "",
    response_model=PaginatedResponse[RemisionRead],
    dependencies=[Depends(require_permission("remisiones.leer"))],
)
def listar_remisiones(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    desde: date | None = Query(None, description="Fecha desde (inclusive)"),
    hasta: date | None = Query(None, description="Fecha hasta (inclusive)"),
    numero_remision: str | None = Query(None),
    numero_orden_servicio: str | None = Query(None),
    tercero_id: int | None = Query(None, description="Coincide como cliente o conductor"),
    placa: str | None = Query(None, description="Placa del vehículo"),
    proyecto_id: int | None = Query(None),
    estado_facturacion: str | None = Query(None),
    factura: str | None = Query(None, description="Número de factura asociada a la remisión"),
    q: str | None = Query(None, description="Búsqueda general: número, cliente, placa o factura"),
    ordenar_por: str | None = Query(None, description="numero_remision, fecha, cliente, estado o placa"),
    sentido: str = Query("asc", pattern="^(asc|desc)$"),
    session: Session = Depends(get_session),
):
    statement = select(Remision)
    if desde:
        statement = statement.where(Remision.fecha >= desde)
    if hasta:
        statement = statement.where(Remision.fecha <= hasta)
    if numero_remision:
        patrones = _patrones_busqueda_numero(numero_remision)
        statement = statement.where(
            or_(*[Remision.numero_remision.ilike(p) for p in patrones])
        )
    if numero_orden_servicio:
        statement = statement.join(
            OrdenServicio, OrdenServicio.id == Remision.orden_servicio_id
        ).where(OrdenServicio.numero.ilike(f"%{numero_orden_servicio}%"))
    if tercero_id:
        statement = statement.where(
            or_(Remision.cliente_id == tercero_id, Remision.conductor_id == tercero_id)
        )
    if placa:
        statement = statement.join(Activo, Activo.id == Remision.vehiculo_id).where(
            Activo.placa.ilike(f"%{placa}%")
        )
    if proyecto_id:
        statement = statement.where(Remision.proyecto_id == proyecto_id)
    if estado_facturacion:
        statement = statement.where(Remision.estado_facturacion == estado_facturacion)
    if factura:
        statement = statement.where(Remision.id.in_(_remision_ids_por_factura(factura)))
    if q:
        patron = f"%{q}%"
        patrones_numero = _patrones_busqueda_numero(q)
        statement = statement.where(
            or_(
                *[Remision.numero_remision.ilike(p) for p in patrones_numero],
                Remision.cliente_id.in_(select(Tercero.id).where(Tercero.nombre.ilike(patron))),
                Remision.vehiculo_id.in_(select(Activo.id).where(Activo.placa.ilike(patron))),
                Remision.id.in_(_remision_ids_por_factura(q)),
            )
        )

    total = session.exec(select(func.count()).select_from(statement.subquery())).one()
    orden = (
        _clausula_orden_remisiones(ordenar_por, sentido)
        if ordenar_por
        else [Remision.fecha.desc(), Remision.id.desc()]
    )
    remisiones = session.exec(
        statement.order_by(*orden)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    items = svc.serializar_remisiones(session, list(remisiones))
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/{remision_id}",
    response_model=RemisionDetalleRead,
    dependencies=[Depends(require_permission("remisiones.leer"))],
)
def obtener_remision(remision_id: int, session: Session = Depends(get_session)):
    remision = _obtener_remision_o_404(session, remision_id)
    return svc.serializar_remision_detalle(session, remision)


@router.post(
    "",
    response_model=RemisionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("remisiones.escribir"))],
)
def crear_remision(
    payload: RemisionCreate,
    usuario: Usuario = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    prefijo = _obtener_prefijo_o_404(session, payload.prefijo_id)
    svc.validar_camabaja(session, payload.tipo_servicio_id, payload.camabaja_id)
    numero_remision, consecutivo = svc.resolver_numero_remision(
        session, payload.numero_remision, prefijo
    )

    remision = Remision(
        numero_remision=numero_remision,
        prefijo_id=payload.prefijo_id,
        consecutivo=consecutivo,
        orden_servicio_id=payload.orden_servicio_id,
        fecha=payload.fecha,
        forma_pago_id=payload.forma_pago_id,
        cliente_id=payload.cliente_id,
        conductor_id=payload.conductor_id,
        origen_municipio_id=payload.origen_municipio_id,
        destino_municipio_id=payload.destino_municipio_id,
        proyecto_id=payload.proyecto_id,
        tramo_id=payload.tramo_id,
        tipo_servicio_id=payload.tipo_servicio_id,
        vehiculo_id=payload.vehiculo_id,
        camabaja_id=payload.camabaja_id,
        kilometros=payload.kilometros,
        hora_salida=payload.hora_salida,
        hora_llegada=payload.hora_llegada,
        remision_agresur=payload.remision_agresur,
        observaciones=payload.observaciones,
        usuario_creador_id=usuario.id,
    )
    session.add(remision)
    flush_or_409(session)

    svc.registrar_auditoria(
        session,
        usuario_id=usuario.id,
        tabla="remisiones",
        registro_id=remision.id,
        accion="CREAR",
        detalle={"numero_remision": remision.numero_remision},
    )
    commit_or_409(session)
    session.refresh(remision)
    return svc.serializar_remision(session, remision)


@router.put(
    "/{remision_id}",
    response_model=RemisionUpdateResponse,
    dependencies=[Depends(require_permission("remisiones.escribir"))],
)
def actualizar_remision(
    remision_id: int,
    payload: RemisionUpdate,
    usuario: Usuario = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    remision = _obtener_remision_o_404(session, remision_id)
    svc.validar_remision_editable(remision)

    datos = payload.model_dump(exclude_unset=True)

    advertencia = None
    if "orden_servicio_id" in datos and datos["orden_servicio_id"] != remision.orden_servicio_id:
        cantidad_eliminados = svc.eliminar_productos_de_remision(session, remision)
        if cantidad_eliminados:
            advertencia = (
                f"Se eliminaron {cantidad_eliminados} producto(s) asociados a la "
                "remisión por el cambio de orden de servicio (regla RN-008)."
            )

    nuevo_tipo_servicio_id = datos.get("tipo_servicio_id", remision.tipo_servicio_id)
    nuevo_camabaja_id = datos.get("camabaja_id", remision.camabaja_id)
    svc.validar_camabaja(session, nuevo_tipo_servicio_id, nuevo_camabaja_id)

    detalle_cambios = {
        campo: {
            "anterior": svc.valor_serializable(getattr(remision, campo)),
            "nuevo": svc.valor_serializable(valor),
        }
        for campo, valor in datos.items()
        if getattr(remision, campo) != valor
    }

    for campo, valor in datos.items():
        setattr(remision, campo, valor)
    session.add(remision)
    flush_or_409(session)

    if detalle_cambios:
        svc.registrar_auditoria(
            session,
            usuario_id=usuario.id,
            tabla="remisiones",
            registro_id=remision.id,
            accion="EDITAR",
            detalle=detalle_cambios,
        )
    commit_or_409(session)
    session.refresh(remision)
    return RemisionUpdateResponse(
        remision=svc.serializar_remision(session, remision), advertencia=advertencia
    )


@router.delete(
    "/{remision_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("remisiones.escribir"))],
)
def eliminar_remision(
    remision_id: int,
    usuario: Usuario = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    remision = _obtener_remision_o_404(session, remision_id)
    if remision.estado_facturacion != "NO_FACTURADA":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "No se puede eliminar la remisión: su estado de facturación es "
                f"'{remision.estado_facturacion}'."
            ),
        )

    svc.eliminar_productos_de_remision(session, remision)
    session.delete(remision)

    svc.registrar_auditoria(
        session,
        usuario_id=usuario.id,
        tabla="remisiones",
        registro_id=remision_id,
        accion="ELIMINAR",
    )
    commit_or_409(session)


@router.post(
    "/{remision_id}/copiar",
    response_model=CopiarRemisionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("remisiones.escribir"))],
)
def copiar_remision(
    remision_id: int,
    payload: CopiarRemisionRequest,
    usuario: Usuario = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    original = _obtener_remision_o_404(session, remision_id)
    prefijo = _obtener_prefijo_o_404(session, original.prefijo_id)
    numero_remision, consecutivo = svc.resolver_numero_remision(
        session, payload.numero_remision, prefijo
    )

    nueva = Remision(
        numero_remision=numero_remision,
        prefijo_id=original.prefijo_id,
        consecutivo=consecutivo,
        orden_servicio_id=original.orden_servicio_id,
        fecha=original.fecha,
        forma_pago_id=original.forma_pago_id,
        cliente_id=original.cliente_id,
        conductor_id=original.conductor_id,
        origen_municipio_id=original.origen_municipio_id,
        destino_municipio_id=original.destino_municipio_id,
        proyecto_id=original.proyecto_id,
        tramo_id=original.tramo_id,
        tipo_servicio_id=original.tipo_servicio_id,
        vehiculo_id=original.vehiculo_id,
        camabaja_id=original.camabaja_id,
        kilometros=original.kilometros,
        hora_salida=original.hora_salida,
        hora_llegada=original.hora_llegada,
        remision_agresur=original.remision_agresur,
        observaciones=original.observaciones,
        usuario_creador_id=usuario.id,
    )
    session.add(nueva)
    flush_or_409(session)

    alerta_saldo_bajo = None
    if payload.copiar_productos:
        productos_originales = session.exec(
            select(RemisionProducto).where(RemisionProducto.remision_id == remision_id)
        ).all()
        for p in productos_originales:
            nuevo_producto = RemisionProducto(
                remision_id=nueva.id,
                producto_id=p.producto_id,
                cantidad=p.cantidad,
                unidad_medida_id=p.unidad_medida_id,
                valor_material=p.valor_material,
                valor_flete=p.valor_flete,
                valor_camabaja=p.valor_camabaja,
                numero_viajes=p.numero_viajes,
                valor_comision=p.valor_comision,
                valor_costo=p.valor_costo,
            )
            session.add(nuevo_producto)
            if nueva.orden_servicio_id is not None and p.valor_flete:
                alerta = svc.aplicar_delta_saldo_orden(
                    session, nueva.orden_servicio_id, p.valor_flete
                )
                if alerta:
                    alerta_saldo_bajo = alerta

    svc.registrar_auditoria(
        session,
        usuario_id=usuario.id,
        tabla="remisiones",
        registro_id=nueva.id,
        accion="CREAR",
        detalle={
            "copiada_de_remision_id": remision_id,
            "copiar_productos": payload.copiar_productos,
        },
    )
    commit_or_409(session)
    session.refresh(nueva)
    return CopiarRemisionResponse(
        remision=svc.serializar_remision_detalle(session, nueva),
        alerta_saldo_bajo=alerta_saldo_bajo,
    )


@router.post(
    "/actualizar-nit",
    response_model=CargaExcelResponse,
    dependencies=[Depends(require_permission("remisiones.actualizar_nit"))],
)
async def actualizar_nit_por_excel(
    file: UploadFile = File(...),
    usuario: Usuario = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    contenido = await leer_excel_subido(file)
    filas_totales, exitosas, errores_count, detalle = nit_excel_svc.procesar_actualizar_nit(
        session, contenido, usuario.id
    )
    session.add(
        CargaExcel(
            tipo="ACTUALIZAR_NIT",
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
