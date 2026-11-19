"""Generación de los reportes descargables en Excel del módulo de Remisiones.

Los encabezados y el orden de columnas son los que pidió el cliente (ver
``backend/app/data_import/formatos/reporte-remisiones-*-programa_nuevo.xlsx``,
columna E de cada archivo) — no se pueden reordenar ni renombrar sin que el
cliente lo confirme. Ver docs/NOTAS_RETOMAR.md / informe de entrega para los
supuestos de mapeo de cada columna "ID".
"""

from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from sqlmodel import Session, func, select

from app.core import numero_remision as numero_remision_svc
from app.models.activo import Activo
from app.models.catalogos import (
    FormaPago,
    Producto,
    Proyecto,
    TipoServicio,
    Tramo,
    UnidadMedida,
)
from app.models.facturacion import Factura, RemisionFacturacion
from app.models.orden_servicio import OrdenServicio
from app.models.remision import Remision, RemisionProducto
from app.models.tercero import Tercero
from app.models.ubicacion import Municipio
from app.models.usuario import Usuario

COLUMNAS_GENERAL = [
    "ID",
    "Numero de remision",
    "Fecha",
    "Forma de pago",
    "ODS",
    "ID del cliente",
    "Cliente",
    "Proyecto",
    "Tramo",
    "Origen",
    "Destino",
    "Kilometros",
    "Vehiculos",
    "Cama Baja",
    "Hora llegada",
    "Hola salida",
    "ID del conductor",
    "Conductor",
    "Tipo de transporte",
    "Observaciones",
    "Id Producto",
    "Producto",
    "Cantidad",
    "Unidad de medida",
    "Valor Material",
    "Valor Flete",
    "Numero de viajes",
    "Valor de comision",
    "Valor de costo",
    "Valor cama baja",
    "Remision AGRESUR",
    "ID del usuario",
    "Usuario",
    "Estado",
]

COLUMNAS_FACTURADAS = [
    "Numero de remision",
    "Fecha",
    "Forma de pago",
    "ODS",
    "ID cliente",
    "Cliente",
    "Proyecto",
    "Tramo",
    "Origen",
    "Destino",
    "Kilometros",
    "Vehiculos",
    "Cama Baja",
    "Hora llegada",
    "Hola salida",
    "Conductor",
    "Tipo de transporte",
    "Usuario",
    "ID usuario",
    "ID factura",
    "Usuario Factura",
    "ID usuario factura",
    "Número de factura",
    "Fecha de factura",
    "Valor flete",
    "Valor Camabaja",
    "Subtotal",
    "Valor Material",
    "Total",
    "Valor facturado",
    "Valor pendiente",
    "Estado",
]

# Columnas que deben quedar como texto aunque el valor sea numérico (para no
# perder ceros a la izquierda ni que Excel las reinterprete).
COLUMNAS_TEXTO = {
    "ID del cliente",
    "ID cliente",
    "ID del conductor",
    "ID del usuario",
    "ID usuario",
    "ID usuario factura",
}

COLUMNAS_FECHA = {"Fecha", "Fecha de factura"}
COLUMNAS_HORA = {"Hora llegada", "Hola salida"}


def _aplicar_filtros(
    statement,
    *,
    desde: date | None,
    hasta: date | None,
    cliente_id: int | None,
    proyecto_id: int | None,
    vehiculo_id: int | None,
    camabaja_id: int | None,
    estado_facturacion: str | None = None,
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
    if estado_facturacion:
        statement = statement.where(Remision.estado_facturacion == estado_facturacion)
    return statement


class _Catalogos:
    """Catálogos en memoria: cada tabla se lee una sola vez (son pocas filas
    comparadas con las remisiones) en vez de una consulta por remisión."""

    def __init__(self, session: Session):
        self.session = session
        self._tablas: dict[type, dict[int, Any]] = {}

    def get(self, modelo: type, id_: int | None):
        if id_ is None:
            return None
        if modelo not in self._tablas:
            self._tablas[modelo] = {o.id: o for o in self.session.exec(select(modelo)).all()}
        return self._tablas[modelo].get(id_)


def _ids(statement):
    """Subconsulta con los ids de las remisiones del statement filtrado."""
    return statement.with_only_columns(Remision.id).order_by(None)


def _lineas_por_remision(session: Session, ids_subq) -> dict[int, list[RemisionProducto]]:
    salida: dict[int, list[RemisionProducto]] = defaultdict(list)
    for linea in session.exec(
        select(RemisionProducto).where(RemisionProducto.remision_id.in_(ids_subq)).order_by(RemisionProducto.id)
    ).all():
        salida[linea.remision_id].append(linea)
    return salida


def _activas_por_remision(session: Session, ids_subq) -> dict[int, list[RemisionFacturacion]]:
    salida: dict[int, list[RemisionFacturacion]] = defaultdict(list)
    for registro in session.exec(
        select(RemisionFacturacion)
        .where(RemisionFacturacion.remision_id.in_(ids_subq), RemisionFacturacion.anulada.is_(False))
        .order_by(RemisionFacturacion.id)
    ).all():
        salida[registro.remision_id].append(registro)
    return salida


def _datos_comunes(cat: _Catalogos, remision: Remision) -> dict[str, Any]:
    cliente = cat.get(Tercero, remision.cliente_id)
    conductor = cat.get(Tercero, remision.conductor_id)
    origen = cat.get(Municipio, remision.origen_municipio_id)
    destino = cat.get(Municipio, remision.destino_municipio_id)
    proyecto = cat.get(Proyecto, remision.proyecto_id)
    tramo = cat.get(Tramo, remision.tramo_id)
    forma_pago = cat.get(FormaPago, remision.forma_pago_id)
    tipo_servicio = cat.get(TipoServicio, remision.tipo_servicio_id)
    vehiculo = cat.get(Activo, remision.vehiculo_id)
    camabaja = cat.get(Activo, remision.camabaja_id)
    usuario_creador = cat.get(Usuario, remision.usuario_creador_id)
    orden_servicio = cat.get(OrdenServicio, remision.orden_servicio_id)

    return {
        "id": remision.id,
        # Forma de las hojas de referencia del cliente: "GTS-006525".
        "numero_remision": numero_remision_svc.para_reporte(remision.numero_remision),
        "fecha": remision.fecha,
        "forma_pago": forma_pago.nombre if forma_pago else None,
        "ods": orden_servicio.numero if orden_servicio else None,
        "cliente_identificacion": cliente.identificacion if cliente else None,
        "cliente_nombre": cliente.nombre if cliente else None,
        "proyecto": proyecto.nombre if proyecto else None,
        "tramo": tramo.nombre if tramo else None,
        "origen": origen.nombre if origen else None,
        "destino": destino.nombre if destino else None,
        "kilometros": remision.kilometros,
        "vehiculo_placa": vehiculo.placa if vehiculo else None,
        "camabaja_placa": camabaja.placa if camabaja else None,
        "hora_llegada": remision.hora_llegada,
        "hora_salida": remision.hora_salida,
        "conductor_identificacion": conductor.identificacion if conductor else None,
        "conductor_nombre": conductor.nombre if conductor else None,
        "tipo_servicio": tipo_servicio.nombre if tipo_servicio else None,
        "observaciones": remision.observaciones,
        "remision_agresur": remision.remision_agresur,
        # Identificación (cédula) del usuario, no su id interno; vacío si
        # el usuario no la tiene cargada (no se inventa).
        "usuario_creador_identificacion": usuario_creador.identificacion if usuario_creador else None,
        "usuario_creador_nombre": usuario_creador.nombre if usuario_creador else None,
        "estado_facturacion": remision.estado_facturacion,
    }


def _totales(productos: list[RemisionProducto]) -> dict[str, Decimal]:
    valor_material = sum((p.valor_material for p in productos), Decimal(0))
    valor_flete = sum((p.valor_flete for p in productos), Decimal(0))
    valor_camabaja = sum((p.valor_camabaja for p in productos), Decimal(0))
    subtotal = valor_flete + valor_camabaja
    return {
        "valor_material": valor_material,
        "valor_flete": valor_flete,
        "valor_camabaja": valor_camabaja,
        "subtotal": subtotal,
        "total": subtotal + valor_material,
    }


def _totales_remision(session: Session, remision_id: int) -> dict[str, Decimal]:
    productos = session.exec(
        select(RemisionProducto).where(RemisionProducto.remision_id == remision_id)
    ).all()
    return _totales(list(productos))


def _celda(ws, nombre: str, valor):
    celda = WriteOnlyCell(ws)
    if nombre in COLUMNAS_TEXTO:
        celda.value = str(valor) if valor is not None else None
        celda.number_format = "@"
    elif nombre in COLUMNAS_FECHA:
        celda.value = valor
        if valor is not None:
            celda.number_format = "yyyy-mm-dd"
    elif nombre in COLUMNAS_HORA:
        celda.value = valor
        if valor is not None:
            celda.number_format = "hh:mm"
    elif isinstance(valor, Decimal):
        # Como en la hoja de referencia: entero si no tiene centavos
        # (250000, no 250000.0); con centavos, tal cual.
        celda.value = int(valor) if valor == valor.to_integral_value() else float(valor)
    else:
        celda.value = valor
    return celda


def _valor_simple(valor):
    """Valor sin formato especial (más rápido que una celda con estilo)."""
    if isinstance(valor, Decimal):
        return int(valor) if valor == valor.to_integral_value() else float(valor)
    return valor


def _escribir_hojas(hojas: list[tuple[str, list[str], list[dict[str, Any]]]], resumen: list[list[Any]] | None = None) -> BytesIO:
    """Libro en modo de solo escritura (rápido y con poca memoria aunque
    tenga decenas de miles de filas). `resumen`, si se pasa, va de primera
    hoja ("Resumen"), sin fila de encabezados y con los títulos en negrita."""
    wb = Workbook(write_only=True)
    if resumen is not None:
        ws = wb.create_sheet(title="Resumen")
        ws.column_dimensions["A"].width = 64
        for letra in "BCD":
            ws.column_dimensions[letra].width = 20
        negrita = Font(bold=True)
        for fila in resumen:
            titulo = isinstance(fila[0], str) and (fila[0].isupper() or fila[0].startswith(("Total", "CIERRE")))
            celdas = []
            for i, valor in enumerate(fila):
                celda = WriteOnlyCell(ws, value=int(valor) if isinstance(valor, Decimal) and valor == valor.to_integral_value() else (float(valor) if isinstance(valor, Decimal) else valor))
                if titulo:
                    celda.font = negrita
                if i == 1 and isinstance(celda.value, (int, float)) and not isinstance(celda.value, bool):
                    celda.number_format = "#,##0.##"
                celdas.append(celda)
            ws.append(celdas)
    for titulo, columnas, filas in hojas:
        ws = wb.create_sheet(title=titulo)
        for col_idx in range(1, len(columnas) + 1):
            ws.column_dimensions[get_column_letter(col_idx)].width = 16
        ws.append(list(columnas))
        con_formato = [n in COLUMNAS_TEXTO or n in COLUMNAS_FECHA or n in COLUMNAS_HORA for n in columnas]
        for fila in filas:
            ws.append(
                [
                    _celda(ws, nombre, fila.get(nombre)) if formato else _valor_simple(fila.get(nombre))
                    for nombre, formato in zip(columnas, con_formato, strict=True)
                ]
            )
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def _escribir_xlsx(filas: list[dict[str, Any]], columnas: list[str]) -> BytesIO:
    return _escribir_hojas([("Sheet1", columnas, filas)])


def generar_reporte_general(
    session: Session,
    *,
    desde: date | None,
    hasta: date | None,
    cliente_id: int | None,
    proyecto_id: int | None,
    vehiculo_id: int | None,
    camabaja_id: int | None,
    estado_facturacion: str | None = None,
) -> BytesIO:
    statement = _aplicar_filtros(
        select(Remision),
        desde=desde,
        hasta=hasta,
        cliente_id=cliente_id,
        proyecto_id=proyecto_id,
        vehiculo_id=vehiculo_id,
        camabaja_id=camabaja_id,
        estado_facturacion=estado_facturacion,
    )
    remisiones = session.exec(statement.order_by(Remision.fecha, Remision.id)).all()
    lineas_por_remision = _lineas_por_remision(session, _ids(statement))
    cat = _Catalogos(session)

    filas: list[dict[str, Any]] = []
    for remision in remisiones:
        comunes = _datos_comunes(cat, remision)
        lineas = lineas_por_remision.get(remision.id, [])

        base_fila = {
            "ID": comunes["id"],
            "Numero de remision": comunes["numero_remision"],
            "Fecha": comunes["fecha"],
            "Forma de pago": comunes["forma_pago"],
            "ODS": comunes["ods"],
            "ID del cliente": comunes["cliente_identificacion"],
            "Cliente": comunes["cliente_nombre"],
            "Proyecto": comunes["proyecto"],
            "Tramo": comunes["tramo"],
            "Origen": comunes["origen"],
            "Destino": comunes["destino"],
            "Kilometros": comunes["kilometros"],
            "Vehiculos": comunes["vehiculo_placa"],
            "Cama Baja": comunes["camabaja_placa"],
            "Hora llegada": comunes["hora_llegada"],
            "Hola salida": comunes["hora_salida"],
            "ID del conductor": comunes["conductor_identificacion"],
            "Conductor": comunes["conductor_nombre"],
            "Tipo de transporte": comunes["tipo_servicio"],
            "Observaciones": comunes["observaciones"],
            "Remision AGRESUR": comunes["remision_agresur"],
            "ID del usuario": comunes["usuario_creador_identificacion"],
            "Usuario": comunes["usuario_creador_nombre"],
            "Estado": comunes["estado_facturacion"],
        }

        if not lineas:
            filas.append(dict(base_fila))
            continue

        for linea in lineas:
            producto = cat.get(Producto, linea.producto_id)
            unidad = cat.get(UnidadMedida, linea.unidad_medida_id)
            fila = dict(base_fila)
            fila.update(
                {
                    "Id Producto": producto.id if producto else None,
                    "Producto": producto.nombre if producto else None,
                    "Cantidad": linea.cantidad,
                    "Unidad de medida": unidad.nombre if unidad else None,
                    "Valor Material": linea.valor_material,
                    "Valor Flete": linea.valor_flete,
                    "Numero de viajes": linea.numero_viajes,
                    "Valor de comision": linea.valor_comision,
                    "Valor de costo": linea.valor_costo,
                    "Valor cama baja": linea.valor_camabaja,
                }
            )
            filas.append(fila)

    return _escribir_xlsx(filas, COLUMNAS_GENERAL)


def _fila_facturada(
    cat: _Catalogos,
    remision: Remision,
    registro: RemisionFacturacion,
    totales: dict[str, Decimal],
    valor_pendiente: Decimal,
) -> dict[str, Any]:
    comunes = _datos_comunes(cat, remision)
    factura = cat.get(Factura, registro.factura_id)
    usuario_facturacion = cat.get(Usuario, registro.usuario_id)
    return {
        "Numero de remision": comunes["numero_remision"],
        "Fecha": comunes["fecha"],
        "Forma de pago": comunes["forma_pago"],
        "ODS": comunes["ods"],
        "ID cliente": comunes["cliente_identificacion"],
        "Cliente": comunes["cliente_nombre"],
        "Proyecto": comunes["proyecto"],
        "Tramo": comunes["tramo"],
        "Origen": comunes["origen"],
        "Destino": comunes["destino"],
        "Kilometros": comunes["kilometros"],
        "Vehiculos": comunes["vehiculo_placa"],
        "Cama Baja": comunes["camabaja_placa"],
        "Hora llegada": comunes["hora_llegada"],
        "Hola salida": comunes["hora_salida"],
        "Conductor": comunes["conductor_nombre"],
        "Tipo de transporte": comunes["tipo_servicio"],
        "Usuario": comunes["usuario_creador_nombre"],
        "ID usuario": comunes["usuario_creador_identificacion"],
        "ID factura": factura.id if factura else None,
        "Usuario Factura": usuario_facturacion.nombre if usuario_facturacion else None,
        "ID usuario factura": usuario_facturacion.identificacion if usuario_facturacion else None,
        "Número de factura": factura.numero_factura if factura else None,
        "Fecha de factura": factura.fecha_factura if factura else None,
        "Valor flete": totales["valor_flete"],
        "Valor Camabaja": totales["valor_camabaja"],
        "Subtotal": totales["subtotal"],
        "Valor Material": totales["valor_material"],
        "Total": totales["total"],
        "Valor facturado": registro.valor_facturado,
        "Valor pendiente": valor_pendiente,
        "Estado": comunes["estado_facturacion"],
    }


def generar_reporte_facturadas(
    session: Session,
    *,
    desde: date | None,
    hasta: date | None,
    cliente_id: int | None,
    proyecto_id: int | None,
    vehiculo_id: int | None,
    camabaja_id: int | None,
    estado_facturacion: str | None = None,
) -> BytesIO:
    statement = _aplicar_filtros(
        select(Remision).where(Remision.estado_facturacion != "NO_FACTURADA"),
        desde=desde,
        hasta=hasta,
        cliente_id=cliente_id,
        proyecto_id=proyecto_id,
        vehiculo_id=vehiculo_id,
        camabaja_id=camabaja_id,
        estado_facturacion=estado_facturacion,
    )
    remisiones = session.exec(statement.order_by(Remision.fecha, Remision.id)).all()
    ids_subq = _ids(statement)
    activas_por_remision = _activas_por_remision(session, ids_subq)
    lineas_por_remision = _lineas_por_remision(session, ids_subq)
    cat = _Catalogos(session)

    filas: list[dict[str, Any]] = []
    for remision in remisiones:
        activas = activas_por_remision.get(remision.id, [])
        if not activas:
            continue  # sin facturación activa que listar
        totales = _totales(lineas_por_remision.get(remision.id, []))
        valor_pendiente = totales["total"] - sum((r.valor_facturado for r in activas), Decimal(0))
        for registro in activas:
            filas.append(_fila_facturada(cat, remision, registro, totales, valor_pendiente))

    return _escribir_xlsx(filas, COLUMNAS_FACTURADAS)


# ── Cierre anual ──────────────────────────────────────────────────────────────

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]
COLUMNAS_CIERRE_FACTURAS = [
    "Número de factura", "Fecha de factura", "ID cliente", "Cliente", "Tipo", "Valor facturado", "Cantidad de remisiones",
]


def serie_de_factura(numero: str) -> str:
    """"F-7-1780" → "F-7"; "L-201-455" → "L-201"; "F-1234" → "F"."""
    partes = numero.split("-")
    return "-".join(partes[:-1]) if len(partes) > 1 else numero


def datos_cierre_anual(session: Session, *, anio: int, base: str = "factura") -> dict[str, Any]:
    """Facturaciones activas del año y sus remisiones.

    base="factura": las facturaciones cuya factura tiene fecha en el año (el
    cierre contable). base="remision": las facturaciones de remisiones con
    fecha en el año, sin importar cuándo se facturaron."""
    inicio, fin = date(anio, 1, 1), date(anio + 1, 1, 1)
    rf, fa, re_ = RemisionFacturacion, Factura, Remision
    consulta = (
        select(rf, fa, re_)
        .join(fa, fa.id == rf.factura_id)
        .join(re_, re_.id == rf.remision_id)
        .where(rf.anulada.is_(False))
    )
    if base == "remision":
        consulta = consulta.where(re_.fecha >= inicio, re_.fecha < fin)
    else:
        consulta = consulta.where(fa.fecha_factura >= inicio, fa.fecha_factura < fin)
    registros = session.exec(consulta.order_by(fa.fecha_factura, fa.numero_factura, re_.fecha, re_.id)).all()

    remisiones_del_anio_otro = session.exec(
        select(re_.id)
        .join(rf, rf.remision_id == re_.id)
        .join(fa, fa.id == rf.factura_id)
        .where(rf.anulada.is_(False), re_.fecha >= inicio, re_.fecha < fin, (fa.fecha_factura < inicio) | (fa.fecha_factura >= fin))
        .distinct()
    ).all()
    remisiones_de_otro_en_facturas_del_anio = session.exec(
        select(re_.id)
        .join(rf, rf.remision_id == re_.id)
        .join(fa, fa.id == rf.factura_id)
        .where(rf.anulada.is_(False), fa.fecha_factura >= inicio, fa.fecha_factura < fin, (re_.fecha < inicio) | (re_.fecha >= fin))
        .distinct()
    ).all()
    estados_del_anio = Counter(
        dict(
            session.exec(
                select(re_.estado_facturacion, func.count(re_.id))
                .where(re_.fecha >= inicio, re_.fecha < fin)
                .group_by(re_.estado_facturacion)
            ).all()
        )
    )
    return {
        "registros": registros,
        "remisiones_del_anio_facturadas_en_otro": len(remisiones_del_anio_otro),
        "remisiones_de_otro_anio_en_facturas_del_anio": len(remisiones_de_otro_en_facturas_del_anio),
        "estados_del_anio": estados_del_anio,
    }


def generar_cierre_anual(session: Session, *, anio: int, base: str = "factura") -> BytesIO:
    datos = datos_cierre_anual(session, anio=anio, base=base)
    registros = datos["registros"]
    cat = _Catalogos(session)

    por_factura: dict[int, dict[str, Any]] = {}
    clientes_por_factura: dict[int, set] = defaultdict(set)

    def grupo() -> dict[str, Any]:
        return {"valor": Decimal(0), "facturas": set(), "remisiones": set()}

    por_mes: dict[int, dict[str, Any]] = {m: grupo() for m in range(1, 13)}
    por_cliente: dict[int, dict[str, Any]] = defaultdict(grupo)
    por_serie: dict[str, dict[str, Any]] = defaultdict(grupo)
    for registro, factura, remision in registros:
        f = por_factura.setdefault(
            factura.id, {"factura": factura, "valor": Decimal(0), "remisiones": set(), "parcial": False}
        )
        f["valor"] += registro.valor_facturado
        f["remisiones"].add(remision.id)
        f["parcial"] = f["parcial"] or registro.tipo_facturacion == "PARCIAL"
        clientes_por_factura[factura.id].add(remision.cliente_id)
        mes = (factura.fecha_factura if base == "factura" else remision.fecha).month
        for agrupado in (por_mes[mes], por_cliente[remision.cliente_id], por_serie[serie_de_factura(factura.numero_factura)]):
            agrupado["valor"] += registro.valor_facturado
            agrupado["facturas"].add(factura.id)
            agrupado["remisiones"].add(remision.id)

    filas_facturas = []
    for fid, f in por_factura.items():
        clientes = clientes_por_factura[fid]
        cliente = cat.get(Tercero, next(iter(clientes))) if len(clientes) == 1 else None
        filas_facturas.append(
            {
                "Número de factura": f["factura"].numero_factura,
                "Fecha de factura": f["factura"].fecha_factura,
                "ID cliente": cliente.identificacion if cliente else None,
                "Cliente": cliente.nombre if cliente else f"VARIOS CLIENTES ({len(clientes)})",
                "Tipo": "PARCIAL" if f["parcial"] else "TOTAL",
                "Valor facturado": f["valor"],
                "Cantidad de remisiones": len(f["remisiones"]),
            }
        )

    # Detalle por remisión facturada (las 32 columnas del reporte de facturadas)
    ids_remisiones = sorted({remision.id for _, _, remision in registros})
    lineas_por_remision: dict[int, list[RemisionProducto]] = defaultdict(list)
    activas_por_remision: dict[int, list[RemisionFacturacion]] = defaultdict(list)
    for i in range(0, len(ids_remisiones), 5000):
        bloque = ids_remisiones[i : i + 5000]
        for linea in session.exec(select(RemisionProducto).where(RemisionProducto.remision_id.in_(bloque))).all():
            lineas_por_remision[linea.remision_id].append(linea)
        for reg in session.exec(
            select(RemisionFacturacion).where(
                RemisionFacturacion.remision_id.in_(bloque), RemisionFacturacion.anulada.is_(False)
            )
        ).all():
            activas_por_remision[reg.remision_id].append(reg)
    filas_detalle = []
    for registro, _factura, remision in registros:
        totales = _totales(lineas_por_remision.get(remision.id, []))
        pendiente = totales["total"] - sum(
            (r.valor_facturado for r in activas_por_remision.get(remision.id, [])), Decimal(0)
        )
        filas_detalle.append(_fila_facturada(cat, remision, registro, totales, pendiente))

    total = sum((f["valor"] for f in por_factura.values()), Decimal(0))
    criterio = "fecha de factura" if base == "factura" else "fecha de la remisión"
    estados = datos["estados_del_anio"]
    resumen: list[dict[str, Any]] = []

    def fila(a=None, b=None, c=None, d=None):
        resumen.append({"A": a, "B": b, "C": c, "D": d})

    fila(f"CIERRE ANUAL {anio}", f"Agrupado por {criterio}")
    fila()
    fila("Total facturado del año", total)
    fila("Cantidad de facturas", len(por_factura))
    fila("Cantidad de remisiones facturadas", len(ids_remisiones))
    fila(f"Remisiones con fecha {anio} sin facturar (NO_FACTURADA)", estados.get("NO_FACTURADA", 0))
    fila(f"Remisiones con fecha {anio} facturadas parcialmente (FACTURADA_PARCIAL)", estados.get("FACTURADA_PARCIAL", 0))
    fila(f"Remisiones con fecha {anio} «No aplica facturación» (NO_APLICA)", estados.get("NO_APLICA", 0))
    fila(f"Remisiones con fecha {anio} facturadas en otro año", datos["remisiones_del_anio_facturadas_en_otro"])
    fila(f"Remisiones de otro año incluidas en facturas de {anio}", datos["remisiones_de_otro_anio_en_facturas_del_anio"])
    fila()
    fila("POR MES", "Valor facturado", "Facturas", "Remisiones")
    for m in range(1, 13):
        fila(MESES[m - 1], por_mes[m]["valor"], len(por_mes[m]["facturas"]), len(por_mes[m]["remisiones"]))
    fila("Total anual", total, len(por_factura), len(ids_remisiones))
    fila()
    fila("POR CLIENTE", "Valor facturado", "Facturas", "Remisiones")
    for cliente_id, g in sorted(por_cliente.items(), key=lambda x: -x[1]["valor"]):
        cliente = cat.get(Tercero, cliente_id)
        fila(cliente.nombre if cliente else None, g["valor"], len(g["facturas"]), len(g["remisiones"]))
    fila()
    fila("POR SERIE DE FACTURA", "Valor facturado", "Facturas", "Remisiones")
    for serie, g in sorted(por_serie.items()):
        fila(serie, g["valor"], len(g["facturas"]), len(g["remisiones"]))

    return _escribir_hojas(
        [
            ("Facturas", COLUMNAS_CIERRE_FACTURAS, filas_facturas),
            ("Detalle", COLUMNAS_FACTURADAS, filas_detalle),
        ],
        resumen=[[f["A"], f["B"], f["C"], f["D"]] for f in resumen],
    )
