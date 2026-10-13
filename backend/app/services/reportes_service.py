"""Generación de los reportes descargables en Excel del módulo de Remisiones."""

from datetime import date
from decimal import Decimal
from io import BytesIO

import pandas as pd
from sqlmodel import Session, select

from app.models.activo import Activo
from app.models.catalogos import Proyecto, TipoServicio, Tramo
from app.models.facturacion import Factura, RemisionFacturacion
from app.models.remision import Remision, RemisionProducto
from app.models.tercero import Tercero
from app.models.ubicacion import Municipio
from app.models.usuario import Usuario

COLUMNAS_GENERAL = [
    "id",
    "fecha",
    "numero_remision",
    "cliente",
    "identificacion_cliente",
    "conductor",
    "origen",
    "destino",
    "proyecto",
    "tramo",
    "tipo_servicio",
    "placa_vehiculo",
    "placa_camabaja",
    "kilometros",
    "valor_material_total",
    "valor_flete_total",
    "valor_camabaja_total",
    "valor_total_remision",
    "usuario_creador",
    "remision_agresur",
    "estado_facturacion",
]

COLUMNAS_FACTURADAS = [
    *COLUMNAS_GENERAL,
    "numero_factura",
    "fecha_factura",
    "usuario_facturacion",
    "valor_facturado",
    "valor_pendiente",
    "tipo_facturacion",
]


def _aplicar_filtros(
    statement,
    *,
    desde: date | None,
    hasta: date | None,
    cliente_id: int | None,
    proyecto_id: int | None,
    vehiculo_id: int | None,
    camabaja_id: int | None,
):
    if desde:
        statement = statement.where(Remision.fecha >= desde)
    if hasta:
        statement = statement.where(Remision.fecha <= hasta)
    if cliente_id:
        statement = statement.where(Remision.cliente_id == cliente_id)
    if proyecto_id:
        statement = statement.where(Remision.proyecto_id == proyecto_id)
    if vehiculo_id:
        statement = statement.where(Remision.vehiculo_id == vehiculo_id)
    if camabaja_id:
        statement = statement.where(Remision.camabaja_id == camabaja_id)
    return statement


def _fila_base(session: Session, remision: Remision) -> dict:
    cliente = session.get(Tercero, remision.cliente_id)
    conductor = session.get(Tercero, remision.conductor_id) if remision.conductor_id else None
    origen = session.get(Municipio, remision.origen_municipio_id)
    destino = session.get(Municipio, remision.destino_municipio_id)
    proyecto = session.get(Proyecto, remision.proyecto_id) if remision.proyecto_id else None
    tramo = session.get(Tramo, remision.tramo_id) if remision.tramo_id else None
    tipo_servicio = (
        session.get(TipoServicio, remision.tipo_servicio_id) if remision.tipo_servicio_id else None
    )
    vehiculo = session.get(Activo, remision.vehiculo_id) if remision.vehiculo_id else None
    camabaja = session.get(Activo, remision.camabaja_id) if remision.camabaja_id else None
    usuario_creador = session.get(Usuario, remision.usuario_creador_id)

    productos = session.exec(
        select(RemisionProducto).where(RemisionProducto.remision_id == remision.id)
    ).all()
    valor_material_total = sum((p.valor_material for p in productos), Decimal(0))
    valor_flete_total = sum((p.valor_flete for p in productos), Decimal(0))
    valor_camabaja_total = sum((p.valor_camabaja for p in productos), Decimal(0))

    return {
        "id": remision.id,
        "fecha": remision.fecha,
        "numero_remision": remision.numero_remision,
        "cliente": cliente.nombre if cliente else None,
        "identificacion_cliente": cliente.identificacion if cliente else None,
        "conductor": conductor.nombre if conductor else None,
        "origen": origen.nombre if origen else None,
        "destino": destino.nombre if destino else None,
        "proyecto": proyecto.nombre if proyecto else None,
        "tramo": tramo.nombre if tramo else None,
        "tipo_servicio": tipo_servicio.nombre if tipo_servicio else None,
        "placa_vehiculo": vehiculo.placa if vehiculo else None,
        "placa_camabaja": camabaja.placa if camabaja else None,
        "kilometros": remision.kilometros,
        "valor_material_total": valor_material_total,
        "valor_flete_total": valor_flete_total,
        "valor_camabaja_total": valor_camabaja_total,
        "valor_total_remision": valor_material_total + valor_flete_total + valor_camabaja_total,
        "usuario_creador": usuario_creador.nombre if usuario_creador else None,
        "remision_agresur": remision.remision_agresur,
        "estado_facturacion": remision.estado_facturacion,
    }


def _generar_xlsx(filas: list[dict], columnas: list[str]) -> BytesIO:
    df = pd.DataFrame(filas, columns=columnas)
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer


def generar_reporte_general(
    session: Session,
    *,
    desde: date | None,
    hasta: date | None,
    cliente_id: int | None,
    proyecto_id: int | None,
    vehiculo_id: int | None,
    camabaja_id: int | None,
) -> BytesIO:
    statement = _aplicar_filtros(
        select(Remision),
        desde=desde,
        hasta=hasta,
        cliente_id=cliente_id,
        proyecto_id=proyecto_id,
        vehiculo_id=vehiculo_id,
        camabaja_id=camabaja_id,
    )
    remisiones = session.exec(statement.order_by(Remision.fecha, Remision.id)).all()
    filas = [_fila_base(session, r) for r in remisiones]
    return _generar_xlsx(filas, COLUMNAS_GENERAL)


def generar_reporte_facturadas(
    session: Session,
    *,
    desde: date | None,
    hasta: date | None,
    cliente_id: int | None,
    proyecto_id: int | None,
    vehiculo_id: int | None,
    camabaja_id: int | None,
) -> BytesIO:
    statement = _aplicar_filtros(
        select(Remision).where(Remision.estado_facturacion != "NO_FACTURADA"),
        desde=desde,
        hasta=hasta,
        cliente_id=cliente_id,
        proyecto_id=proyecto_id,
        vehiculo_id=vehiculo_id,
        camabaja_id=camabaja_id,
    )
    remisiones = session.exec(statement.order_by(Remision.fecha, Remision.id)).all()

    filas: list[dict] = []
    for remision in remisiones:
        base = _fila_base(session, remision)
        activas = session.exec(
            select(RemisionFacturacion).where(
                RemisionFacturacion.remision_id == remision.id,
                RemisionFacturacion.anulada.is_(False),
            )
        ).all()
        if not activas:
            continue  # estado inconsistente puntual; no hay facturación activa que listar
        valor_facturado_acumulado = sum((r.valor_facturado for r in activas), Decimal(0))
        valor_pendiente = base["valor_total_remision"] - valor_facturado_acumulado
        for registro in activas:
            factura = session.get(Factura, registro.factura_id)
            usuario_facturacion = (
                session.get(Usuario, registro.usuario_id) if registro.usuario_id else None
            )
            fila = dict(base)
            fila.update(
                {
                    "numero_factura": factura.numero_factura if factura else None,
                    "fecha_factura": factura.fecha_factura if factura else None,
                    "usuario_facturacion": usuario_facturacion.nombre if usuario_facturacion else None,
                    "valor_facturado": registro.valor_facturado,
                    "valor_pendiente": valor_pendiente,
                    "tipo_facturacion": registro.tipo_facturacion,
                }
            )
            filas.append(fila)
    return _generar_xlsx(filas, COLUMNAS_FACTURADAS)
