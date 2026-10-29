"""Reglas de negocio del módulo de Remisiones. Aislado de los routers para
que cada regla se pueda ubicar, probar y ajustar de forma independiente.
"""

from datetime import date, time
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import aliased
from sqlmodel import Session, func, select

from app.models.activo import Activo
from app.models.auditoria import Auditoria
from app.models.catalogos import Prefijo, Producto, TipoServicio, UnidadMedida
from app.models.orden_servicio import OrdenServicio
from app.models.remision import Remision, RemisionProducto
from app.models.tercero import Tercero
from app.models.ubicacion import Municipio
from app.schemas.remision import ProductoRemisionRead, RemisionDetalleRead, RemisionRead

NOMBRE_TIPO_SERVICIO_CAMABAJA = "Cama baja"
INTENTOS_MAXIMOS_NUMERO_REMISION = 5
UMBRAL_ALERTA_SALDO_BAJO = Decimal("0.10")


# --- numeración ---


def _verificar_numero_remision_unico(session: Session, numero_remision: str) -> None:
    existente = session.exec(
        select(Remision).where(Remision.numero_remision == numero_remision)
    ).first()
    if existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una remisión con numero_remision '{numero_remision}'",
        )


def generar_numero_remision_automatico(
    session: Session, prefijo: Prefijo
) -> tuple[str, str]:
    """Genera numero_remision a partir de prefijo.codigo + consecutivo_actual,
    incrementando el consecutivo. Si hay colisión (no debería ocurrir en
    operación normal), reintenta hasta INTENTOS_MAXIMOS_NUMERO_REMISION veces.
    """
    consecutivo_base = prefijo.consecutivo_actual
    for _ in range(INTENTOS_MAXIMOS_NUMERO_REMISION):
        consecutivo_base += 1
        consecutivo_str = f"{consecutivo_base:06d}"
        numero_remision = f"{prefijo.codigo}-{consecutivo_str}"
        existe = session.exec(
            select(Remision).where(Remision.numero_remision == numero_remision)
        ).first()
        if existe is None:
            prefijo.consecutivo_actual = consecutivo_base
            session.add(prefijo)
            return numero_remision, consecutivo_str
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=(
            f"No se pudo generar un numero_remision único para el prefijo "
            f"'{prefijo.codigo}' tras {INTENTOS_MAXIMOS_NUMERO_REMISION} intentos. "
            "Contacte al administrador del sistema."
        ),
    )


def resolver_numero_remision(
    session: Session, numero_remision_input: str | None, prefijo: Prefijo
) -> tuple[str, str]:
    """Decide el numero_remision y el consecutivo a persistir.

    - Si el prefijo es manual (remisión de papel), numero_remision es
      obligatorio en el request y se usa tal cual (puede ser alfanumérico).
    - Si se provee numero_remision explícitamente (aunque el prefijo no sea
      manual), se usa tal cual.
    - En cualquier otro caso, se autogenera a partir del consecutivo del
      prefijo.
    """
    if prefijo.es_manual:
        if not numero_remision_input:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"El prefijo '{prefijo.codigo}' es manual (remisión de papel): "
                    "numero_remision es obligatorio."
                ),
            )
        _verificar_numero_remision_unico(session, numero_remision_input)
        return numero_remision_input, numero_remision_input

    if numero_remision_input:
        _verificar_numero_remision_unico(session, numero_remision_input)
        return numero_remision_input, numero_remision_input

    return generar_numero_remision_automatico(session, prefijo)


# --- reglas de negocio ---


def validar_camabaja(
    session: Session, tipo_servicio_id: int | None, camabaja_id: int | None
) -> None:
    """El tipo de servicio 'Cama baja' exige camabaja_id; cualquier otro tipo
    debe dejarlo en NULL."""
    tipo_camabaja = session.exec(
        select(TipoServicio).where(TipoServicio.nombre == NOMBRE_TIPO_SERVICIO_CAMABAJA)
    ).first()
    es_camabaja = tipo_camabaja is not None and tipo_servicio_id == tipo_camabaja.id

    if es_camabaja and camabaja_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El tipo de servicio 'Cama baja' requiere especificar camabaja_id.",
        )
    if not es_camabaja and camabaja_id is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="camabaja_id solo puede diligenciarse cuando el tipo de servicio es 'Cama baja'.",
        )


def validar_remision_editable(remision: Remision) -> None:
    """Aislada a propósito: una remisión FACTURADA (totalmente) no se puede
    editar; FACTURADA_PARCIAL sí. Si el cliente refina esta regla más
    adelante, el ajuste queda contenido aquí."""
    if remision.estado_facturacion == "FACTURADA":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La remisión está totalmente facturada (FACTURADA) y no puede editarse.",
        )


def actualizar_nit_remision(
    session: Session, remision: Remision, nuevo_cliente_id: int, usuario_id: int | None
) -> dict[str, int]:
    """HU-022 / RN-028 / RN-029 / RN-030: reasigna remisiones.cliente_id sin
    importar estado_facturacion (a propósito NO llama validar_remision_editable)
    y sin tocar facturas ni remision_facturacion — solo cambia esa columna."""
    cliente_anterior = remision.cliente_id
    remision.cliente_id = nuevo_cliente_id
    session.add(remision)
    registrar_auditoria(
        session,
        usuario_id=usuario_id,
        tabla="remisiones",
        registro_id=remision.id,
        accion="ACTUALIZAR_NIT",
        detalle={"cliente_id_anterior": cliente_anterior, "cliente_id_nuevo": nuevo_cliente_id},
    )
    return {"cliente_id_anterior": cliente_anterior, "cliente_id_nuevo": nuevo_cliente_id}


def aplicar_delta_saldo_orden(
    session: Session, orden_servicio_id: int | None, delta: Decimal
) -> str | None:
    """Aplica un delta de consumo contra el saldo de la orden de servicio.
    delta > 0 consume saldo (se resta), delta < 0 lo devuelve (se suma).
    Rechaza con 400 si el descuento dejaría el saldo en negativo. Devuelve
    un mensaje de alerta si el saldo resultante queda por debajo del 10% del
    valor_tope original, o None si no aplica."""
    if orden_servicio_id is None or delta == 0:
        return None

    orden = session.get(OrdenServicio, orden_servicio_id)
    if orden is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró la orden de servicio con id {orden_servicio_id}",
        )

    nuevo_saldo = orden.saldo_disponible - delta
    if nuevo_saldo < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"El valor_flete excede el saldo disponible de la orden de servicio "
                f"'{orden.numero}'. Saldo disponible actual: {orden.saldo_disponible}."
            ),
        )

    orden.saldo_disponible = nuevo_saldo
    session.add(orden)

    if orden.valor_tope > 0 and nuevo_saldo < orden.valor_tope * UMBRAL_ALERTA_SALDO_BAJO:
        return (
            f"Saldo bajo en la orden de servicio '{orden.numero}': quedan "
            f"{nuevo_saldo} disponibles (menos del 10% del valor tope de {orden.valor_tope})."
        )
    return None


def eliminar_productos_de_remision(session: Session, remision: Remision) -> int:
    """Revierte el saldo consumido (si la remisión estaba ligada a una orden
    de servicio) y elimina todos los remision_productos de la remisión.
    Devuelve la cantidad de productos eliminados."""
    productos = session.exec(
        select(RemisionProducto).where(RemisionProducto.remision_id == remision.id)
    ).all()
    if not productos:
        return 0

    if remision.orden_servicio_id is not None:
        total_flete = sum((p.valor_flete for p in productos), Decimal(0))
        if total_flete:
            aplicar_delta_saldo_orden(session, remision.orden_servicio_id, -total_flete)

    for producto in productos:
        session.delete(producto)
    return len(productos)


def registrar_auditoria(
    session: Session,
    *,
    usuario_id: int | None,
    tabla: str,
    registro_id: int,
    accion: str,
    detalle: dict[str, Any] | None = None,
) -> None:
    session.add(
        Auditoria(
            tabla=tabla,
            registro_id=registro_id,
            accion=accion,
            usuario_id=usuario_id,
            detalle_json=detalle or {},
        )
    )


def valor_serializable(valor: Any) -> Any:
    """Convierte tipos no serializables directamente a JSON (Decimal, date,
    time) a texto, para poder guardarlos en detalle_json."""
    if isinstance(valor, (Decimal, date, time)):
        return str(valor)
    return valor


# --- serialización (joins explícitos, sin Relationship() de SQLModel) ---


def calcular_valor_total(session: Session, remision_id: int) -> Decimal:
    """Valor total de una remisión: suma de (valor_material + valor_flete +
    valor_camabaja) de todas sus líneas, SIN multiplicar por numero_viajes
    (los valores de cada línea ya son el total de todos sus viajes).

    Única definición de la regla (decisión del cliente, 2026-10-27): la usan
    la API de remisiones y facturación (facturacion_service la llama). El
    listado la replica en SQL en serializar_remisiones; una prueba verifica
    que ambas den lo mismo."""
    productos = session.exec(
        select(RemisionProducto).where(RemisionProducto.remision_id == remision_id)
    ).all()
    return sum(
        (p.valor_material + p.valor_flete + p.valor_camabaja for p in productos),
        Decimal(0),
    )


def serializar_remision(session: Session, remision: Remision) -> RemisionRead:
    cliente = session.get(Tercero, remision.cliente_id)
    conductor = session.get(Tercero, remision.conductor_id) if remision.conductor_id else None
    origen = session.get(Municipio, remision.origen_municipio_id)
    destino = session.get(Municipio, remision.destino_municipio_id)
    vehiculo = session.get(Activo, remision.vehiculo_id) if remision.vehiculo_id else None
    return _remision_read(
        remision,
        cliente_nombre=cliente.nombre if cliente else None,
        conductor_nombre=conductor.nombre if conductor else None,
        origen_nombre=origen.nombre if origen else None,
        destino_nombre=destino.nombre if destino else None,
        vehiculo_placa=vehiculo.placa if vehiculo else None,
        valor_total=calcular_valor_total(session, remision.id),
    )


def subconsulta_valor_total():
    """calcular_valor_total en SQL (correlacionada con Remision), para el
    listado y para ordenar por valor total en el servidor."""
    rp = RemisionProducto
    return (
        select(func.coalesce(func.sum(rp.valor_material + rp.valor_flete + rp.valor_camabaja), 0))
        .where(rp.remision_id == Remision.id)
        .correlate(Remision)
        .scalar_subquery()
    )


def serializar_remisiones(session: Session, remisiones: list[Remision]) -> list[RemisionRead]:
    """Lo mismo que serializar_remision para una lista, pero con UNA sola
    consulta para toda la página (nombres por JOIN y valor total por
    subconsulta), en vez de ~6 por fila. Usada por el listado; la prueba
    tests/test_listado_remisiones.py verifica que dé idéntico."""
    if not remisiones:
        return []
    cliente, conductor = aliased(Tercero), aliased(Tercero)
    origen, destino = aliased(Municipio), aliased(Municipio)
    valor_total = subconsulta_valor_total()
    filas = session.exec(
        select(
            Remision.id,
            cliente.nombre,
            conductor.nombre,
            origen.nombre,
            destino.nombre,
            Activo.placa,
            valor_total,
        )
        .outerjoin(cliente, cliente.id == Remision.cliente_id)
        .outerjoin(conductor, conductor.id == Remision.conductor_id)
        .outerjoin(origen, origen.id == Remision.origen_municipio_id)
        .outerjoin(destino, destino.id == Remision.destino_municipio_id)
        .outerjoin(Activo, Activo.id == Remision.vehiculo_id)
        .where(Remision.id.in_([r.id for r in remisiones]))
    ).all()
    por_id = {fila[0]: fila[1:] for fila in filas}
    resultado = []
    for remision in remisiones:
        cli, cond, ori, dest, placa, total = por_id[remision.id]
        resultado.append(
            _remision_read(
                remision,
                cliente_nombre=cli,
                conductor_nombre=cond,
                origen_nombre=ori,
                destino_nombre=dest,
                vehiculo_placa=placa,
                valor_total=total,
            )
        )
    return resultado


def _remision_read(
    remision: Remision,
    *,
    cliente_nombre: str | None,
    conductor_nombre: str | None,
    origen_nombre: str | None,
    destino_nombre: str | None,
    vehiculo_placa: str | None,
    valor_total: Decimal,
) -> RemisionRead:
    return RemisionRead(
        id=remision.id,
        numero_remision=remision.numero_remision,
        prefijo_id=remision.prefijo_id,
        consecutivo=remision.consecutivo,
        orden_servicio_id=remision.orden_servicio_id,
        fecha=remision.fecha,
        forma_pago_id=remision.forma_pago_id,
        cliente_id=remision.cliente_id,
        cliente_nombre=cliente_nombre,
        conductor_id=remision.conductor_id,
        conductor_nombre=conductor_nombre,
        origen_municipio_id=remision.origen_municipio_id,
        origen_municipio_nombre=origen_nombre,
        destino_municipio_id=remision.destino_municipio_id,
        destino_municipio_nombre=destino_nombre,
        proyecto_id=remision.proyecto_id,
        tramo_id=remision.tramo_id,
        tipo_servicio_id=remision.tipo_servicio_id,
        vehiculo_id=remision.vehiculo_id,
        vehiculo_placa=vehiculo_placa,
        camabaja_id=remision.camabaja_id,
        kilometros=remision.kilometros,
        hora_salida=remision.hora_salida,
        hora_llegada=remision.hora_llegada,
        remision_agresur=remision.remision_agresur,
        observaciones=remision.observaciones,
        usuario_creador_id=remision.usuario_creador_id,
        estado_facturacion=remision.estado_facturacion,
        valor_total=valor_total,
        creado_en=remision.creado_en,
        actualizado_en=remision.actualizado_en,
    )


def serializar_producto(session: Session, producto: RemisionProducto) -> ProductoRemisionRead:
    prod = session.get(Producto, producto.producto_id)
    unidad = (
        session.get(UnidadMedida, producto.unidad_medida_id)
        if producto.unidad_medida_id
        else None
    )
    return ProductoRemisionRead(
        id=producto.id,
        remision_id=producto.remision_id,
        producto_id=producto.producto_id,
        producto_nombre=prod.nombre if prod else None,
        cantidad=producto.cantidad,
        unidad_medida_id=producto.unidad_medida_id,
        unidad_medida_nombre=unidad.nombre if unidad else None,
        valor_material=producto.valor_material,
        valor_flete=producto.valor_flete,
        valor_camabaja=producto.valor_camabaja,
        numero_viajes=producto.numero_viajes,
        valor_comision=producto.valor_comision,
        valor_costo=producto.valor_costo,
    )


def serializar_remision_detalle(session: Session, remision: Remision) -> RemisionDetalleRead:
    base = serializar_remision(session, remision)
    productos = session.exec(
        select(RemisionProducto).where(RemisionProducto.remision_id == remision.id)
    ).all()
    return RemisionDetalleRead(
        **base.model_dump(),
        productos=[serializar_producto(session, p) for p in productos],
    )
