"""Reglas de negocio del módulo de Facturación. recalcular_estado_facturacion
es la única fuente de verdad de remision.estado_facturacion: cualquier
creación, anulación o modificación de un remision_facturacion debe terminar
llamándola, y ningún otro punto del código debe tocar ese campo a mano.
"""

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.core.errors import flush_or_409
from app.models.auditoria import Auditoria
from app.models.facturacion import Factura, RemisionFacturacion
from app.models.remision import Remision, RemisionProducto
from app.schemas.facturacion import (
    FacturaRead,
    RemisionFacturacionHistorialRead,
    RemisionFacturacionRead,
    ResumenFacturasRead,
)

NUMERO_FACTURA_REGEX = re.compile(r"^[A-Z]-\d+$")


# --- valores base ---


def calcular_valor_total_remision(session: Session, remision_id: int) -> Decimal:
    """valor_total_remision = suma de (valor_material + valor_flete +
    valor_camabaja) de todos sus remision_productos."""
    productos = session.exec(
        select(RemisionProducto).where(RemisionProducto.remision_id == remision_id)
    ).all()
    return sum(
        (p.valor_material + p.valor_flete + p.valor_camabaja for p in productos),
        Decimal(0),
    )


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
                "(ej. 'F-1234'): una letra mayúscula, un guion y dígitos."
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
    remision_facturacion.anulada_en = datetime.utcnow()
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
    return RemisionFacturacionRead(
        id=registro.id,
        remision_id=registro.remision_id,
        numero_remision=remision.numero_remision if remision else None,
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
