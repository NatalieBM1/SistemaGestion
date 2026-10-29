"""Reglas de negocio del módulo de Facturación. recalcular_estado_facturacion
es la única fuente de verdad de remision.estado_facturacion: cualquier
creación, anulación o modificación de un remision_facturacion debe terminar
llamándola, y ningún otro punto del código debe tocar ese campo a mano.
"""

import re
from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.core.errors import flush_or_409
from app.core.fechas import ahora_utc
from app.models.auditoria import Auditoria
from app.models.facturacion import Factura, RemisionFacturacion
from app.models.remision import Remision
from app.models.tercero import Tercero
from app.schemas.facturacion import (
    FacturaRead,
    RemisionFacturacionHistorialRead,
    RemisionFacturacionRead,
    ResumenFacturasRead,
)
from app.services.remision_service import calcular_valor_total

# Acepta el formato histórico ("F-1234": letra, guion, dígitos) y el
# formato real vigente del cliente ("F-7-468": letra, guion, dígitos,
# guion, dígitos) — nunca se invalidan ni se tocan las facturas ya
# cargadas con el formato corto.
NUMERO_FACTURA_REGEX = re.compile(r"^[A-Z]-\d+(-\d+)?$")


# --- valores base ---


def calcular_valor_total_remision(session: Session, remision_id: int) -> Decimal:
    """Valor total de la remisión. La regla vive en un solo lugar:
    remision_service.calcular_valor_total."""
    return calcular_valor_total(session, remision_id)


def calcular_valor_facturado_activo(session: Session, remision_id: int) -> Decimal:
    registros = session.exec(
        select(RemisionFacturacion).where(
            RemisionFacturacion.remision_id == remision_id,
            RemisionFacturacion.anulada.is_(False),
        )
    ).all()
    return sum((r.valor_facturado for r in registros), Decimal(0))


def recalcular_estado_facturacion(session: Session, remision_id: int) -> str:
    """Única fuente de verdad de remision.estado_facturacion."""
    remision = session.get(Remision, remision_id)
    if remision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró la remisión con id {remision_id}",
        )
    valor_total = calcular_valor_total_remision(session, remision_id)
    valor_facturado = calcular_valor_facturado_activo(session, remision_id)

    if valor_facturado == 0:
        nuevo_estado = "NO_FACTURADA"
    elif valor_facturado < valor_total:
        nuevo_estado = "FACTURADA_PARCIAL"
    else:
        nuevo_estado = "FACTURADA"

    remision.estado_facturacion = nuevo_estado
    session.add(remision)
    return nuevo_estado


# --- auxiliares ---


def validar_formato_numero_factura(numero_factura: str) -> None:
    if not NUMERO_FACTURA_REGEX.match(numero_factura):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"numero_factura '{numero_factura}' no cumple el formato esperado "
                "(ej. 'F-7-468' o 'F-1234'): una letra mayúscula, guion, dígitos, "
                "y opcionalmente otro guion y más dígitos."
            ),
        )


def obtener_o_crear_factura(
    session: Session, numero_factura: str, fecha_factura: date
) -> Factura:
    """RN-015: una factura puede cubrir varias remisiones. Si el número ya
    existe se reutiliza tal cual (no se pisa su fecha)."""
    factura = session.exec(
        select(Factura).where(Factura.numero_factura == numero_factura)
    ).first()
    if factura is not None:
        return factura
    factura = Factura(numero_factura=numero_factura, fecha_factura=fecha_factura)
    session.add(factura)
    flush_or_409(session)
    return factura


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


# --- facturación ---


def facturar_remision(
    session: Session,
    *,
    remision: Remision,
    numero_factura: str,
    fecha_factura: date,
    tipo: str,
    valor_facturado_input: Decimal | None,
    usuario_id: int | None,
) -> RemisionFacturacion:
    validar_formato_numero_factura(numero_factura)

    if remision.estado_facturacion == "FACTURADA":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"La remisión {remision.numero_remision} ya está FACTURADA en su "
                "totalidad; no se puede facturar de más."
            ),
        )

    valor_total = calcular_valor_total_remision(session, remision.id)
    if valor_total <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"La remisión {remision.numero_remision} no tiene productos "
                "(valor_total_remision = 0); no hay nada que facturar."
            ),
        )
    valor_facturado_actual = calcular_valor_facturado_activo(session, remision.id)
    saldo_pendiente = valor_total - valor_facturado_actual

    if tipo == "TOTAL":
        existe_total_activa = session.exec(
            select(RemisionFacturacion).where(
                RemisionFacturacion.remision_id == remision.id,
                RemisionFacturacion.tipo_facturacion == "TOTAL",
                RemisionFacturacion.anulada.is_(False),
            )
        ).first()
        if existe_total_activa is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"La remisión {remision.numero_remision} ya tiene una "
                    "facturación TOTAL activa; no puede duplicarse."
                ),
            )
        valor_a_facturar = saldo_pendiente
    else:  # PARCIAL
        if valor_facturado_input is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="valor_facturado es obligatorio cuando tipo='PARCIAL'.",
            )
        valor_a_facturar = valor_facturado_input
        if valor_a_facturar <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="valor_facturado debe ser mayor que cero.",
            )
        if valor_a_facturar > saldo_pendiente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El valor_facturado ({valor_a_facturar}) supera el saldo "
                    f"pendiente de la remisión {remision.numero_remision} "
                    f"({saldo_pendiente})."
                ),
            )

    factura = obtener_o_crear_factura(session, numero_factura, fecha_factura)

    remision_facturacion = RemisionFacturacion(
        remision_id=remision.id,
        factura_id=factura.id,
        tipo_facturacion=tipo,
        valor_facturado=valor_a_facturar,
        usuario_id=usuario_id,
    )
    session.add(remision_facturacion)
    flush_or_409(session)

    recalcular_estado_facturacion(session, remision.id)

    registrar_auditoria(
        session,
        usuario_id=usuario_id,
        tabla="remisiones",
        registro_id=remision.id,
        accion="FACTURAR",
        detalle={
            "numero_factura": numero_factura,
            "tipo_facturacion": tipo,
            "valor_facturado": str(valor_a_facturar),
        },
    )
    return remision_facturacion


def _validar_seleccion_para_facturar_multiple(
    session: Session, remision_ids: list[int]
) -> tuple[list[Remision], list[dict[str, Any]], int | None]:
    """Valida la selección de remisiones para facturar en bloque, sin
    escribir nada. Devuelve (remisiones_validas, errores_por_remision,
    cliente_id_comun). Si hay algún error (incluido cliente distinto),
    `remisiones_validas` queda vacía — es todo o nada."""
    if not remision_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Selecciona al menos una remisión.",
        )

    remisiones: list[Remision] = []
    errores: list[dict[str, Any]] = []
    for rid in remision_ids:
        remision = session.get(Remision, rid)
        if remision is None:
            errores.append({"remision_id": rid, "numero_remision": None, "motivo": "No existe."})
            continue
        remisiones.append(remision)

    if not remisiones:
        return [], errores, None

    clientes_distintos = {r.cliente_id for r in remisiones}
    if len(clientes_distintos) > 1:
        # Cliente de referencia: el de la primera remisión seleccionada.
        # Con clientes distintos no se factura nada; se marca cada
        # remisión según si coincide o no con esa referencia, para que
        # quede claro cuál(es) sobran de la selección.
        cliente_referencia = remisiones[0].cliente_id
        for r in remisiones:
            motivo = (
                "No se facturó: hay remisiones de otro cliente en la selección."
                if r.cliente_id == cliente_referencia
                else "Es de un cliente distinto al de las demás remisiones seleccionadas."
            )
            errores.append({"remision_id": r.id, "numero_remision": r.numero_remision, "motivo": motivo})
        return [], errores, None

    cliente_id = remisiones[0].cliente_id

    for r in remisiones:
        if r.estado_facturacion == "FACTURADA":
            errores.append(
                {
                    "remision_id": r.id,
                    "numero_remision": r.numero_remision,
                    "motivo": "Ya está FACTURADA en su totalidad.",
                }
            )
            continue
        valor_total = calcular_valor_total_remision(session, r.id)
        if valor_total <= 0:
            errores.append(
                {
                    "remision_id": r.id,
                    "numero_remision": r.numero_remision,
                    "motivo": "No tiene productos; no hay nada que facturar.",
                }
            )

    if errores:
        return [], errores, None

    return remisiones, [], cliente_id


def resumen_seleccion_para_facturar(
    session: Session, remision_ids: list[int]
) -> dict[str, Any]:
    """Vista previa (no escribe nada): cuántas remisiones se pueden
    facturar juntas, el valor total, y el motivo de cada una que no se
    pueda."""
    remisiones_validas, errores, cliente_id = _validar_seleccion_para_facturar_multiple(
        session, remision_ids
    )
    cliente_nombre = None
    items: list[dict[str, Any]] = []
    valor_total = Decimal(0)

    if remisiones_validas:
        cliente = session.get(Tercero, cliente_id)
        cliente_nombre = cliente.nombre if cliente else None
        for r in remisiones_validas:
            saldo = calcular_valor_total_remision(session, r.id) - calcular_valor_facturado_activo(
                session, r.id
            )
            valor_total += saldo
            items.append(
                {
                    "remision_id": r.id,
                    "numero_remision": r.numero_remision,
                    "saldo_pendiente": saldo,
                    "motivo_error": None,
                }
            )
    else:
        items = [
            {
                "remision_id": e["remision_id"],
                "numero_remision": e.get("numero_remision"),
                "saldo_pendiente": None,
                "motivo_error": e["motivo"],
            }
            for e in errores
        ]

    return {
        "puede_facturar": bool(remisiones_validas) and not errores,
        "cliente_id": cliente_id if remisiones_validas else None,
        "cliente_nombre": cliente_nombre,
        "cantidad_remisiones": len(remisiones_validas),
        "valor_total": valor_total,
        "items": items,
    }


def facturar_multiples_remisiones(
    session: Session,
    *,
    remision_ids: list[int],
    numero_factura: str,
    fecha_factura: date,
    usuario_id: int | None,
) -> dict[str, Any]:
    """Registra UNA factura para varias remisiones del mismo cliente, cada
    una por su saldo pendiente (tipo TOTAL). Todo o nada: si cualquier
    remisión no se puede facturar, no se escribe ninguna."""
    validar_formato_numero_factura(numero_factura)

    remisiones_validas, errores, _ = _validar_seleccion_para_facturar_multiple(
        session, remision_ids
    )
    if errores or not remisiones_validas:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"mensaje": "No se facturó ninguna remisión.", "errores": errores},
        )

    valor_total = Decimal(0)
    for remision in remisiones_validas:
        registro = facturar_remision(
            session,
            remision=remision,
            numero_factura=numero_factura,
            fecha_factura=fecha_factura,
            tipo="TOTAL",
            valor_facturado_input=None,
            usuario_id=usuario_id,
        )
        valor_total += registro.valor_facturado

    return {
        "numero_factura": numero_factura,
        "cantidad_remisiones": len(remisiones_validas),
        "valor_total": valor_total,
        "remisiones_ids": [r.id for r in remisiones_validas],
    }


def agregar_remisiones_a_factura(
    session: Session,
    *,
    numero_factura: str,
    remision_ids: list[int],
    usuario_id: int | None,
) -> dict[str, Any]:
    """Agrega remisiones a una factura YA EXISTENTE (cada una por su saldo
    pendiente, tipo TOTAL). Todo o nada: valida mismo cliente de la
    factura, que no estén ya FACTURADA ni ya en esta factura."""
    factura = session.exec(
        select(Factura).where(Factura.numero_factura == numero_factura)
    ).first()
    if factura is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró ninguna factura con numero_factura '{numero_factura}'.",
        )
    if not remision_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Selecciona al menos una remisión.",
        )

    activas_existentes = session.exec(
        select(RemisionFacturacion).where(
            RemisionFacturacion.factura_id == factura.id,
            RemisionFacturacion.anulada.is_(False),
        )
    ).all()
    remisiones_ya_en_factura = {r.remision_id for r in activas_existentes}
    cliente_factura_id: int | None = None
    if activas_existentes:
        primera = session.get(Remision, activas_existentes[0].remision_id)
        cliente_factura_id = primera.cliente_id if primera else None

    remisiones: list[Remision] = []
    errores: list[dict[str, Any]] = []
    for rid in remision_ids:
        remision = session.get(Remision, rid)
        if remision is None:
            errores.append({"remision_id": rid, "numero_remision": None, "motivo": "No existe."})
            continue
        if remision.id in remisiones_ya_en_factura:
            errores.append(
                {"remision_id": remision.id, "numero_remision": remision.numero_remision, "motivo": "Ya está en esta factura."}
            )
            continue
        if remision.estado_facturacion == "FACTURADA":
            errores.append(
                {"remision_id": remision.id, "numero_remision": remision.numero_remision, "motivo": "Ya está FACTURADA en su totalidad."}
            )
            continue
        if cliente_factura_id is not None and remision.cliente_id != cliente_factura_id:
            errores.append(
                {"remision_id": remision.id, "numero_remision": remision.numero_remision, "motivo": "Es de un cliente distinto al de la factura."}
            )
            continue
        valor_total = calcular_valor_total_remision(session, remision.id)
        if valor_total <= 0:
            errores.append(
                {"remision_id": remision.id, "numero_remision": remision.numero_remision, "motivo": "No tiene productos; no hay nada que facturar."}
            )
            continue
        remisiones.append(remision)
        if cliente_factura_id is None:
            cliente_factura_id = remision.cliente_id

    if errores:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"mensaje": "No se agregó ninguna remisión.", "errores": errores},
        )

    valor_agregado = Decimal(0)
    for remision in remisiones:
        registro = facturar_remision(
            session,
            remision=remision,
            numero_factura=numero_factura,
            fecha_factura=factura.fecha_factura,
            tipo="TOTAL",
            valor_facturado_input=None,
            usuario_id=usuario_id,
        )
        valor_agregado += registro.valor_facturado

    return {
        "numero_factura": numero_factura,
        "remisiones_agregadas": len(remisiones),
        "valor_agregado": valor_agregado,
        "remisiones_ids": [r.id for r in remisiones],
    }


def quitar_remision_de_factura(
    session: Session,
    *,
    numero_factura: str,
    remision_id: int,
    usuario_id: int | None,
) -> None:
    factura = session.exec(
        select(Factura).where(Factura.numero_factura == numero_factura)
    ).first()
    if factura is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró ninguna factura con numero_factura '{numero_factura}'.",
        )
    registro = session.exec(
        select(RemisionFacturacion).where(
            RemisionFacturacion.factura_id == factura.id,
            RemisionFacturacion.remision_id == remision_id,
            RemisionFacturacion.anulada.is_(False),
        )
    ).first()
    if registro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La remisión {remision_id} no está activa en la factura '{numero_factura}'.",
        )
    anular_facturacion(session, registro, usuario_id=usuario_id)


def anular_facturacion(
    session: Session,
    remision_facturacion: RemisionFacturacion,
    *,
    usuario_id: int | None,
) -> None:
    if remision_facturacion.anulada:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta facturación ya estaba anulada.",
        )
    remision_facturacion.anulada = True
    remision_facturacion.anulada_en = ahora_utc()
    session.add(remision_facturacion)
    flush_or_409(session)

    recalcular_estado_facturacion(session, remision_facturacion.remision_id)

    registrar_auditoria(
        session,
        usuario_id=usuario_id,
        tabla="remisiones",
        registro_id=remision_facturacion.remision_id,
        accion="ANULAR_FACTURA",
        detalle={"remision_facturacion_id": remision_facturacion.id},
    )


def actualizar_factura(
    session: Session,
    *,
    numero_factura_actual: str,
    numero_factura_nuevo: str | None,
    fecha_factura_nueva: date | None,
    usuario_id: int | None,
) -> tuple[Factura, list[int]]:
    """RN-025/RN-026: actualiza el registro de factura compartido; afecta a
    todas las remisiones asociadas automáticamente."""
    factura = session.exec(
        select(Factura).where(Factura.numero_factura == numero_factura_actual)
    ).first()
    if factura is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró ninguna factura con numero_factura '{numero_factura_actual}'.",
        )

    remisiones_ids = list(
        session.exec(
            select(RemisionFacturacion.remision_id).where(
                RemisionFacturacion.factura_id == factura.id,
                RemisionFacturacion.anulada.is_(False),
            )
        ).all()
    )
    if not remisiones_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La factura '{numero_factura_actual}' no tiene remisiones activas asociadas.",
        )

    if numero_factura_nuevo is not None and numero_factura_nuevo != factura.numero_factura:
        validar_formato_numero_factura(numero_factura_nuevo)
        existente = session.exec(
            select(Factura).where(Factura.numero_factura == numero_factura_nuevo)
        ).first()
        if existente is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe una factura con numero_factura '{numero_factura_nuevo}'.",
            )
        factura.numero_factura = numero_factura_nuevo

    if fecha_factura_nueva is not None:
        factura.fecha_factura = fecha_factura_nueva

    session.add(factura)
    flush_or_409(session)

    registrar_auditoria(
        session,
        usuario_id=usuario_id,
        tabla="facturas",
        registro_id=factura.id,
        accion="ACTUALIZAR",
        detalle={
            "numero_factura_actual": numero_factura_actual,
            "numero_factura_nuevo": numero_factura_nuevo,
            "fecha_factura_nueva": str(fecha_factura_nueva) if fecha_factura_nueva else None,
            "remisiones_afectadas": remisiones_ids,
        },
    )
    return factura, remisiones_ids


# --- serialización ---


def serializar_factura(session: Session, factura: Factura) -> FacturaRead:
    activos = session.exec(
        select(RemisionFacturacion).where(
            RemisionFacturacion.factura_id == factura.id,
            RemisionFacturacion.anulada.is_(False),
        )
    ).all()
    cantidad_remisiones = len({r.remision_id for r in activos})
    valor_total_facturado = sum((r.valor_facturado for r in activos), Decimal(0))
    return FacturaRead(
        numero_factura=factura.numero_factura,
        fecha_factura=factura.fecha_factura,
        cantidad_remisiones=cantidad_remisiones,
        valor_total_facturado=valor_total_facturado,
    )


def serializar_remision_facturacion(
    session: Session, registro: RemisionFacturacion
) -> RemisionFacturacionRead:
    remision = session.get(Remision, registro.remision_id)
    cliente = session.get(Tercero, remision.cliente_id) if remision else None
    return RemisionFacturacionRead(
        id=registro.id,
        remision_id=registro.remision_id,
        numero_remision=remision.numero_remision if remision else None,
        cliente_id=remision.cliente_id if remision else None,
        cliente_nombre=cliente.nombre if cliente else None,
        tipo_facturacion=registro.tipo_facturacion,
        valor_facturado=registro.valor_facturado,
        anulada=registro.anulada,
        anulada_en=registro.anulada_en,
        creado_en=registro.creado_en,
    )


def resumen_facturado(
    session: Session, *, desde: date | None, hasta: date | None
) -> ResumenFacturasRead:
    """Suma valor_facturado de las facturaciones activas cuya factura cae en
    el rango [desde, hasta] por fecha_factura. Usado por el dashboard para
    no tener que traer todas las facturas al frontend solo para sumarlas."""
    statement = (
        select(RemisionFacturacion)
        .join(Factura, Factura.id == RemisionFacturacion.factura_id)
        .where(RemisionFacturacion.anulada.is_(False))
    )
    if desde:
        statement = statement.where(Factura.fecha_factura >= desde)
    if hasta:
        statement = statement.where(Factura.fecha_factura <= hasta)
    registros = session.exec(statement).all()
    return ResumenFacturasRead(
        valor_total_facturado=sum((r.valor_facturado for r in registros), Decimal(0)),
        cantidad_facturaciones=len(registros),
    )


def listar_historial_facturacion_de_remision(
    session: Session, remision_id: int
) -> list[RemisionFacturacionHistorialRead]:
    registros = session.exec(
        select(RemisionFacturacion)
        .where(RemisionFacturacion.remision_id == remision_id)
        .order_by(RemisionFacturacion.creado_en.desc())
    ).all()
    resultado = []
    for registro in registros:
        factura = session.get(Factura, registro.factura_id)
        resultado.append(
            RemisionFacturacionHistorialRead(
                id=registro.id,
                remision_id=registro.remision_id,
                numero_remision=None,
                tipo_facturacion=registro.tipo_facturacion,
                valor_facturado=registro.valor_facturado,
                anulada=registro.anulada,
                anulada_en=registro.anulada_en,
                creado_en=registro.creado_en,
                numero_factura=factura.numero_factura if factura else "—",
                fecha_factura=factura.fecha_factura if factura else registro.creado_en.date(),
            )
        )
    return resultado
