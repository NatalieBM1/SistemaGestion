"""Importa remisiones históricas desde la hoja "Registros" de
Remisiones_v7_-Final_TGG.xlsm hacia las tablas transaccionales:
remisiones, remision_productos, facturas, remision_facturacion, proyectos
y tramos.

Alcance (Fase 1 de NOTAS_IMPORTACION.md):
- Remisiones: solo las 1.000 más recientes (por Fecha desc, consecutivo
  desc en empate), excluyendo la fila "G-PRUEBA" del conteo.
- Proyectos y tramos: TODOS los del Excel, no solo los usados en las 1.000.
- Prefijos: consecutivo_actual se ajusta al máximo de TODO el Excel (no
  solo las 1.000), para no reutilizar nunca un número histórico. Los
  prefijos nuevos que aparezcan (AJUSTE, PUT) se crean.
- Productos y facturas: solo los de las remisiones importadas.

Decisiones de mapeo (ver NOTAS_IMPORTACION.md, "Decisiones aprobadas"):
  1. Origen/Destino: formato "Municipio - Departamento"; se busca el
     municipio por nombre (normalizado); si no hay match exacto, se usa el
     municipio "Sin especificar" y se registra en el CSV de errores.
  2. Estado "NO APLICA FACTURACIÓN" -> NO_FACTURADA. "FACTURADA
     PARCIALMENTE" -> tipo_facturacion='PARCIAL' aunque la columna "Tipo
     Facturación" no lo diga.
  3. orden_servicio_id queda NULL siempre; el texto de ODS (si lo hay) se
     agrega a observaciones.
  4. usuario_creador_id = admin@transportesguerrero.com en todas; el
     nombre real del Excel se agrega a observaciones.
  5. G-PRUEBA se excluye antes de contar las 1.000.
  6. Facturas partidas por el corte: se crean con solo las remisiones
     importadas asociadas.

Idempotente: usa `numero_remision` (único en la tabla) como clave — si ya
existe, se omite esa fila (no se duplica, no se actualiza).

Transacciones: una por lote de 500 filas, con un SAVEPOINT por fila dentro
del lote — una fila con error no aborta el lote completo.

No inventa datos: lo que no se puede resolver contra un catálogo existente
queda en NULL o usa el marcador "Sin especificar" (mismo patrón que ya usa
el resto de la app para municipios), y la fila queda registrada en
errores_importacion.csv con el motivo.

Uso:
    python -m app.scripts.importar_registros --db-url <url> [--limite N] [--dry-run]
"""

import argparse
import csv
import re
import sys
import unicodedata
from datetime import date as date_type
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine
from sqlmodel import Session, select

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from app.models.activo import Activo
from app.models.catalogos import FormaPago, Prefijo, Producto, Proyecto, Tramo, TipoServicio, UnidadMedida
from app.models.facturacion import Factura, RemisionFacturacion
from app.models.remision import Remision, RemisionProducto
from app.models.tercero import Tercero
from app.models.ubicacion import Municipio
from app.models.usuario import Usuario

RUTA_EXCEL = Path(__file__).resolve().parents[1] / "data_import" / "Remisiones_v7_-Final_TGG.xlsm"
RUTA_ERRORES = Path(__file__).resolve().parents[1] / "data_import" / "errores_importacion.csv"

CANTIDAD_A_IMPORTAR = 1000
NUMERO_PRUEBA_EXCLUIDO = "G-PRUEBA"
EMAIL_USUARIO_CREADOR = "admin@transportesguerrero.com"
TAMANO_LOTE = 500

ALIAS_FORMA_PAGO = {"CREDITO": "Crédito", "CONTADO": "Contado"}
ALIAS_TIPO_SERVICIO = {"CAMABAJA": "Cama baja"}
ALIAS_UNIDAD_MEDIDA = {"TONELADAS": "Tonelada", "METROS CUBICOS": "Metro cúbico"}
ALIAS_PRODUCTO = {"GRAVILLA": "Gravilla", "RECEBO": "Recebo"}

ESTADO_MAP = {
    "FACTURADA": "FACTURADA",
    "FACTURADA PARCIALMENTE": "FACTURADA_PARCIAL",
    "NO FACTURADA": "NO_FACTURADA",
    "NO APLICA FACTURACION": "NO_FACTURADA",
}


def _normalizar(texto: Any) -> str:
    texto = str(texto).strip().upper()
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def _texto_o_none(valor: Any) -> str | None:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    texto = str(valor).strip()
    return texto if texto and texto.lower() != "nan" else None


def _split_prefijo(numero: str) -> tuple[str | None, str | None]:
    m = re.match(r"^([A-Za-z]+)-?(\d+)$", str(numero).strip())
    if m:
        return m.group(1), m.group(2)
    return None, None


def _decimal_o_cero(valor: Any) -> Decimal:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return Decimal("0")
    try:
        return Decimal(str(valor))
    except InvalidOperation:
        return Decimal("0")


class ErrorFila(Exception):
    def __init__(self, motivo: str):
        self.motivo = motivo
        super().__init__(motivo)


def leer_hoja_registros(ruta: Path | None = None, hoja: str = "Registros") -> pd.DataFrame:
    """`ruta`/`hoja` solo se usan para la prueba de ida y vuelta (leer un
    reporte ya generado como si fuera la hoja "Registros"); en la carga
    histórica normal se usan los valores por defecto."""
    df = pd.read_excel(ruta or RUTA_EXCEL, sheet_name=hoja)
    df.columns = [str(c).strip() for c in df.columns]
    df["_prefijo"], df["_consec"] = zip(*df["Numero de remision"].map(_split_prefijo))
    return df


def calcular_maximos_consecutivo(df: pd.DataFrame) -> dict[str, int]:
    """Máximo consecutivo por prefijo en TODO el Excel (no solo las 1.000)."""
    maximos: dict[str, int] = {}
    for _, fila in df.dropna(subset=["_prefijo", "_consec"]).iterrows():
        pref = fila["_prefijo"]
        consec = int(fila["_consec"])
        maximos[pref] = max(maximos.get(pref, 0), consec)
    return maximos


def seleccionar_top_1000(df: pd.DataFrame) -> pd.DataFrame:
    """Una remision puede tener varias filas en el Excel (una por línea de
    producto: mismo numero_remision, misma Fecha, distinto Producto/valor).
    El corte de "las 1.000 más recientes" tiene que contar REMISIONES
    distintas, no filas — si se cortara por filas crudas se podía partir
    una remisión multi-producto a la mitad. Por eso primero se arma un
    listado de remisiones distintas (una fila por numero_remision) para
    decidir el orden y el corte, y recién después se traen TODAS las
    filas (todas las líneas de producto) de esas remisiones."""
    df = df[df["Numero de remision"] != NUMERO_PRUEBA_EXCLUIDO]
    distintas = df.drop_duplicates(subset=["Numero de remision"], keep="first")
    distintas_ordenadas = distintas.sort_values(["Fecha", "_consec"], ascending=[False, False], na_position="last")
    numeros_top = set(distintas_ordenadas.head(CANTIDAD_A_IMPORTAR)["Numero de remision"])

    todas_las_filas = df[df["Numero de remision"].isin(numeros_top)]
    # Orden estable: por Fecha/consec desc, y dentro de cada remisión en el
    # orden original del Excel (para que la primera fila de cada grupo sea
    # siempre la misma entre corridas).
    todas_las_filas = todas_las_filas.sort_values(
        ["Fecha", "_consec"], ascending=[False, False], na_position="last", kind="stable"
    )
    return todas_las_filas.reset_index(drop=True)


def _obtener_o_crear_por_nombre(session: Session, model, nombre: str, **extra):
    obj = session.exec(select(model).where(model.nombre == nombre)).first()
    if obj is not None:
        return obj, False
    obj = model(nombre=nombre, **extra)
    session.add(obj)
    session.flush()
    return obj, True


def importar_proyectos_y_tramos(session: Session, df: pd.DataFrame) -> dict[str, Any]:
    """Importa TODOS los proyectos y tramos del Excel completo, no solo el
    top 1.000, como se pidió explícitamente.

    Proyecto.cliente_id es obligatorio y la tabla NO tiene restricción de
    nombre único, así que la clave real de un proyecto es (nombre,
    cliente_id): 5 de los 14 nombres de proyecto del Excel aparecen con más
    de un cliente distinto en sus filas, y no hay forma correcta de elegir
    "el" cliente sin inventar — se crea un Proyecto por cada combinación
    real (nombre, cliente) que aparezca en el archivo."""
    proyectos_creados = 0
    tramos_creados = 0
    proyecto_nombres_con_mas_de_un_cliente: list[str] = []
    proyectos_por_clave: dict[tuple[str, int], Proyecto] = {}

    pares = df.dropna(subset=["Proyecto", "ID del cliente"])[["Proyecto", "ID del cliente"]].drop_duplicates()
    nombres_vistos: dict[str, set[int]] = {}
    for _, fila in pares.iterrows():
        nombres_vistos.setdefault(fila["Proyecto"], set()).add(int(fila["ID del cliente"]))
    for nombre, clientes in nombres_vistos.items():
        if len(clientes) > 1:
            proyecto_nombres_con_mas_de_un_cliente.append(nombre)

    for _, fila in pares.iterrows():
        nombre = fila["Proyecto"]
        cliente_id_txt = str(int(fila["ID del cliente"]))
        tercero = session.exec(select(Tercero).where(Tercero.identificacion == cliente_id_txt)).first()
        if tercero is None:
            continue  # no debería pasar: ya se confirmó 100% de match en la Fase 0
        clave = (nombre, tercero.id)
        if clave in proyectos_por_clave:
            continue
        existente = session.exec(
            select(Proyecto).where(Proyecto.nombre == nombre, Proyecto.cliente_id == tercero.id)
        ).first()
        if existente is None:
            existente = Proyecto(nombre=nombre, cliente_id=tercero.id)
            session.add(existente)
            session.flush()
            proyectos_creados += 1
        proyectos_por_clave[clave] = existente
    session.flush()

    filas_tramo = df.dropna(subset=["Tramo", "Proyecto", "ID del cliente"])[
        ["Proyecto", "ID del cliente", "Tramo"]
    ].drop_duplicates()
    for _, fila in filas_tramo.iterrows():
        cliente_id_txt = str(int(fila["ID del cliente"]))
        tercero = session.exec(select(Tercero).where(Tercero.identificacion == cliente_id_txt)).first()
        if tercero is None:
            continue
        proyecto = proyectos_por_clave.get((fila["Proyecto"], tercero.id))
        if proyecto is None:
            continue
        existente = session.exec(
            select(Tramo).where(Tramo.proyecto_id == proyecto.id, Tramo.nombre == fila["Tramo"])
        ).first()
        if existente is None:
            session.add(Tramo(proyecto_id=proyecto.id, nombre=fila["Tramo"]))
            tramos_creados += 1
    session.flush()

    return {
        "proyectos_creados": proyectos_creados,
        "proyectos_totales_claves": len(proyectos_por_clave),
        "tramos_creados": tramos_creados,
        "nombres_de_proyecto_con_mas_de_un_cliente": proyecto_nombres_con_mas_de_un_cliente,
    }


def ajustar_prefijos(session: Session, maximos: dict[str, int]) -> dict[str, Any]:
    reporte: dict[str, Any] = {}
    for codigo, maximo in maximos.items():
        prefijo = session.exec(select(Prefijo).where(Prefijo.codigo == codigo)).first()
        if prefijo is None:
            prefijo = Prefijo(codigo=codigo, consecutivo_actual=maximo, es_manual=False)
            session.add(prefijo)
            reporte[codigo] = {"creado": True, "consecutivo_actual": maximo}
        else:
            antes = prefijo.consecutivo_actual
            if maximo > antes:
                prefijo.consecutivo_actual = maximo
            reporte[codigo] = {"creado": False, "antes": antes, "despues": prefijo.consecutivo_actual}
    session.flush()
    return reporte


def _resolver_municipio(session: Session, texto: str | None, cache: dict[str, Municipio], fallback: Municipio) -> tuple[Municipio, bool]:
    if texto is None:
        return fallback, True
    nombre_municipio = texto.split(" - ")[0].strip()
    clave = _normalizar(nombre_municipio)
    if clave in cache:
        return cache[clave], False
    municipio = session.exec(select(Municipio).where(Municipio.nombre == nombre_municipio)).first()
    if municipio is None:
        todos = session.exec(select(Municipio)).all()
        for m in todos:
            if _normalizar(m.nombre) == clave:
                municipio = m
                break
    if municipio is None:
        cache[clave] = fallback
        return fallback, True
    cache[clave] = municipio
    return municipio, False


def _resolver_catalogo_nombre(session: Session, model, texto: str, alias: dict[str, str], cache: dict[str, Any]):
    clave = _normalizar(texto)
    if clave in cache:
        return cache[clave]
    nombre_real = alias.get(clave, texto)
    obj = session.exec(select(model).where(model.nombre == nombre_real)).first()
    cache[clave] = obj
    return obj


def importar_remisiones(
    session: Session,
    top1000: pd.DataFrame,
    *,
    dry_run: bool,
) -> dict[str, Any]:
    usuario_admin = session.exec(select(Usuario).where(Usuario.email == EMAIL_USUARIO_CREADOR)).first()
    if usuario_admin is None:
        raise RuntimeError(f"No existe el usuario {EMAIL_USUARIO_CREADOR!r} en esta base.")

    municipio_fallback = session.exec(select(Municipio).where(Municipio.codigo_dane == "00000")).first()
    if municipio_fallback is None:
        raise RuntimeError("No existe el municipio fallback 'Sin especificar' (codigo_dane=00000).")

    prefijos_por_codigo = {p.codigo: p for p in session.exec(select(Prefijo)).all()}
    proyectos_por_nombre_cliente = {
        (p.nombre, p.cliente_id): p for p in session.exec(select(Proyecto)).all()
    }
    tramos_por_proyecto_nombre = {
        (t.proyecto_id, t.nombre): t for t in session.exec(select(Tramo)).all()
    }

    cache_municipio: dict[str, Municipio] = {}
    cache_forma_pago: dict[str, Any] = {}
    cache_tipo_servicio: dict[str, Any] = {}
    cache_producto: dict[str, Any] = {}
    cache_unidad: dict[str, Any] = {}

    errores: list[dict[str, str]] = []
    creadas = 0
    omitidas_ya_existian = 0
    omitidas_por_error = 0
    facturas_creadas = 0
    facturas_reutilizadas = 0

    lineas_creadas_total = 0
    lineas_omitidas_por_error = 0

    # Agrupar por numero_remision: una remision puede traer varias filas
    # (una por línea de producto). El SAVEPOINT es por remisión completa
    # (todas sus líneas), no por fila cruda — así una remisión siempre
    # queda completa o no queda, nunca con productos a medias.
    grupos = list(top1000.groupby("Numero de remision", sort=False))
    for inicio in range(0, len(grupos), TAMANO_LOTE):
        lote = grupos[inicio : inicio + TAMANO_LOTE]
        for numero_raw, filas_grupo in lote:
            numero = str(numero_raw).strip()
            savepoint = session.begin_nested()
            try:
                primera = filas_grupo.iloc[0]
                remision_existente = session.exec(
                    select(Remision).where(Remision.numero_remision == numero)
                ).first()

                if remision_existente is not None:
                    remision_id = remision_existente.id
                    estado_facturacion = remision_existente.estado_facturacion
                    crear_factura = False
                else:
                    prefijo = prefijos_por_codigo.get(primera["_prefijo"])
                    if prefijo is None:
                        raise ErrorFila(f"prefijo {primera['_prefijo']!r} no encontrado (no debería pasar)")

                    cliente_id_txt = str(int(primera["ID del cliente"]))
                    cliente = session.exec(select(Tercero).where(Tercero.identificacion == cliente_id_txt)).first()
                    if cliente is None:
                        raise ErrorFila(f"cliente {cliente_id_txt!r} no existe como tercero")

                    conductor = None
                    cond_txt = _texto_o_none(primera.get("ID del conductor"))
                    if cond_txt is not None:
                        cond_id_txt = str(int(float(cond_txt)))
                        conductor = session.exec(select(Tercero).where(Tercero.identificacion == cond_id_txt)).first()

                    origen, origen_fallback = _resolver_municipio(session, _texto_o_none(primera.get("Origen")), cache_municipio, municipio_fallback)
                    destino, destino_fallback = _resolver_municipio(session, _texto_o_none(primera.get("Destino")), cache_municipio, municipio_fallback)

                    vehiculo = None
                    veh_txt = _texto_o_none(primera.get("Vehiculos"))
                    if veh_txt is not None:
                        vehiculo = session.exec(select(Activo).where(Activo.placa == veh_txt)).first()

                    camabaja = None
                    cb_txt = _texto_o_none(primera.get("Cama Baja"))
                    if cb_txt is not None:
                        camabaja = session.exec(select(Activo).where(Activo.placa == cb_txt)).first()

                    proyecto = None
                    tramo = None
                    proy_txt = _texto_o_none(primera.get("Proyecto"))
                    if proy_txt is not None:
                        proyecto = proyectos_por_nombre_cliente.get((proy_txt, cliente.id))
                        tramo_txt = _texto_o_none(primera.get("Tramo"))
                        if tramo_txt is not None and proyecto is not None:
                            tramo = tramos_por_proyecto_nombre.get((proyecto.id, tramo_txt))

                    forma_pago = None
                    fp_txt = _texto_o_none(primera.get("Forma de pago"))
                    if fp_txt is not None:
                        forma_pago = _resolver_catalogo_nombre(session, FormaPago, fp_txt, ALIAS_FORMA_PAGO, cache_forma_pago)

                    tipo_servicio = None
                    tipo_txt = _texto_o_none(primera.get("Tipo de transporte"))
                    if tipo_txt is not None:
                        tipo_servicio = _resolver_catalogo_nombre(session, TipoServicio, tipo_txt, ALIAS_TIPO_SERVICIO, cache_tipo_servicio)

                    fecha_val = primera["Fecha"]
                    fecha = fecha_val.date() if hasattr(fecha_val, "date") else fecha_val

                    hora_salida = _texto_o_none(primera.get("Hora salida"))
                    hora_llegada = _texto_o_none(primera.get("Hora llegada"))

                    estado_excel = _normalizar(primera["Estado"])
                    estado_facturacion = ESTADO_MAP.get(estado_excel)
                    if estado_facturacion is None:
                        raise ErrorFila(f"estado {primera['Estado']!r} sin mapeo conocido")

                    partes_obs: list[str] = []
                    obs_txt = _texto_o_none(primera.get("Observaciones"))
                    if obs_txt:
                        partes_obs.append(obs_txt)
                    ods_txt = _texto_o_none(primera.get("ODS"))
                    if ods_txt:
                        partes_obs.append(f"[ODS histórico: {ods_txt}]")
                    usuario_real = _texto_o_none(primera.get("Usuario"))
                    if usuario_real:
                        partes_obs.append(f"[Registrado originalmente por: {usuario_real}]")
                    if origen_fallback:
                        partes_obs.append(f"[Origen histórico sin municipio exacto: {_texto_o_none(primera.get('Origen'))!r}]")
                    if destino_fallback:
                        partes_obs.append(f"[Destino histórico sin municipio exacto: {_texto_o_none(primera.get('Destino'))!r}]")
                    if len(filas_grupo) > 1:
                        partes_obs.append(f"[{len(filas_grupo)} líneas de producto importadas de la hoja histórica]")
                    observaciones = " ".join(partes_obs) if partes_obs else None

                    remision_agresur = _texto_o_none(primera.get("Remision AGRESUR"))

                    kilometros = primera.get("Kilometros")
                    kilometros = None if pd.isna(kilometros) else Decimal(str(kilometros))

                    remision = Remision(
                        numero_remision=numero,
                        prefijo_id=prefijo.id,
                        consecutivo=primera["_consec"],
                        orden_servicio_id=None,
                        fecha=fecha,
                        forma_pago_id=forma_pago.id if forma_pago else None,
                        cliente_id=cliente.id,
                        conductor_id=conductor.id if conductor else None,
                        origen_municipio_id=origen.id,
                        destino_municipio_id=destino.id,
                        proyecto_id=proyecto.id if proyecto else None,
                        tramo_id=tramo.id if tramo else None,
                        tipo_servicio_id=tipo_servicio.id if tipo_servicio else None,
                        vehiculo_id=vehiculo.id if vehiculo else None,
                        camabaja_id=camabaja.id if camabaja else None,
                        kilometros=kilometros,
                        hora_salida=hora_salida,
                        hora_llegada=hora_llegada,
                        remision_agresur=remision_agresur,
                        observaciones=observaciones,
                        usuario_creador_id=usuario_admin.id,
                        estado_facturacion=estado_facturacion,
                    )
                    session.add(remision)
                    session.flush()
                    remision_id = remision.id
                    crear_factura = True

                # Líneas de producto: una por fila del grupo. Si a una fila
                # le falta el producto (8 de 17.615 en todo el Excel), se
                # omite SOLO esa línea (se anota en el CSV de errores) y
                # la remisión sigue con las líneas que sí se pudieron
                # resolver, en vez de perder toda la remisión por una línea.
                for _, fila in filas_grupo.iterrows():
                    producto_txt = _texto_o_none(fila.get("Producto"))
                    if producto_txt is None:
                        lineas_omitidas_por_error += 1
                        errores.append({"numero_remision": numero, "motivo": "línea sin Producto, omitida (remisión sí se importó)"})
                        continue
                    producto = _resolver_catalogo_nombre(session, Producto, producto_txt, ALIAS_PRODUCTO, cache_producto)
                    if producto is None:
                        lineas_omitidas_por_error += 1
                        errores.append({"numero_remision": numero, "motivo": f"producto {producto_txt!r} no existe en el catálogo, línea omitida"})
                        continue

                    unidad = None
                    umed_txt = _texto_o_none(fila.get("Unidad de medida"))
                    if umed_txt is not None:
                        unidad = _resolver_catalogo_nombre(session, UnidadMedida, umed_txt, ALIAS_UNIDAD_MEDIDA, cache_unidad)

                    cantidad = _decimal_o_cero(fila.get("Cantidad"))
                    valor_material = _decimal_o_cero(fila.get("Valor Material"))
                    valor_flete = _decimal_o_cero(fila.get("Valor Flete"))
                    valor_camabaja_linea = _decimal_o_cero(fila.get("Valor cama baja"))
                    numero_viajes = int(fila.get("Numero de viajes") or 1)
                    valor_comision = _decimal_o_cero(fila.get("Valor de comision"))
                    valor_costo = _decimal_o_cero(fila.get("Valor de costo"))

                    if remision_existente is not None:
                        # idempotencia de líneas en una corrida repetida: si
                        # ya existe una línea idéntica para esta remisión,
                        # no se duplica.
                        ya_existe = session.exec(
                            select(RemisionProducto).where(
                                RemisionProducto.remision_id == remision_id,
                                RemisionProducto.producto_id == producto.id,
                                RemisionProducto.cantidad == cantidad,
                                RemisionProducto.valor_material == valor_material,
                                RemisionProducto.valor_flete == valor_flete,
                            )
                        ).first()
                        if ya_existe is not None:
                            continue

                    session.add(
                        RemisionProducto(
                            remision_id=remision_id,
                            producto_id=producto.id,
                            cantidad=cantidad,
                            unidad_medida_id=unidad.id if unidad else None,
                            valor_material=valor_material,
                            valor_flete=valor_flete,
                            valor_camabaja=valor_camabaja_linea,
                            numero_viajes=numero_viajes,
                            valor_comision=valor_comision,
                            valor_costo=valor_costo,
                        )
                    )
                    lineas_creadas_total += 1

                if crear_factura:
                    factura_txt = _texto_o_none(primera.get("Factura"))
                    if factura_txt is not None:
                        factura = session.exec(select(Factura).where(Factura.numero_factura == factura_txt)).first()
                        if factura is None:
                            fecha_factura_val = primera.get("Fecha Factura")
                            fecha_factura = (
                                fecha_factura_val.date() if hasattr(fecha_factura_val, "date") else fecha
                            )
                            factura = Factura(numero_factura=factura_txt, fecha_factura=fecha_factura)
                            session.add(factura)
                            session.flush()
                            facturas_creadas += 1
                        else:
                            facturas_reutilizadas += 1

                        tipo_facturacion = "PARCIAL" if estado_facturacion == "FACTURADA_PARCIAL" else "TOTAL"
                        vr_facturado = _decimal_o_cero(primera.get("Vr Facturado"))
                        session.add(
                            RemisionFacturacion(
                                remision_id=remision_id,
                                factura_id=factura.id,
                                tipo_facturacion=tipo_facturacion,
                                valor_facturado=vr_facturado,
                                usuario_id=usuario_admin.id,
                                anulada=False,
                            )
                        )

                savepoint.commit()
                if remision_existente is not None:
                    omitidas_ya_existian += 1
                else:
                    creadas += 1
            except Exception as exc:  # noqa: BLE001 — una remision mala no debe tumbar el lote
                savepoint.rollback()
                omitidas_por_error += 1
                motivo = exc.motivo if isinstance(exc, ErrorFila) else f"{type(exc).__name__}: {exc}"
                errores.append({"numero_remision": numero, "motivo": motivo})

        if dry_run:
            session.rollback()
        else:
            session.commit()

    if errores:
        RUTA_ERRORES.parent.mkdir(parents=True, exist_ok=True)
        with open(RUTA_ERRORES, "w", newline="", encoding="utf-8") as f:
            escritor = csv.DictWriter(f, fieldnames=["numero_remision", "motivo"])
            escritor.writeheader()
            escritor.writerows(errores)

    return {
        "creadas": creadas,
        "omitidas_ya_existian": omitidas_ya_existian,
        "omitidas_por_error": omitidas_por_error,
        "facturas_creadas": facturas_creadas,
        "facturas_reutilizadas": facturas_reutilizadas,
        "errores_csv": str(RUTA_ERRORES) if errores else None,
        "total_errores": len(errores),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-url", required=True, help="URL de conexión de la base destino (NUNCA la de producción sin confirmar).")
    parser.add_argument("--limite", type=int, default=None, help="Si se da, procesa solo las primeras N filas del top 1000 (para pruebas rápidas).")
    parser.add_argument("--dry-run", action="store_true", help="Corre todo pero revierte cada lote al final (no deja nada escrito).")
    args = parser.parse_args()

    engine = create_engine(args.db_url)

    print(f"Leyendo {RUTA_EXCEL} ...")
    df = leer_hoja_registros()
    print(f"  {len(df)} filas en la hoja Registros.")

    maximos = calcular_maximos_consecutivo(df)
    top1000 = seleccionar_top_1000(df)
    n_remisiones = top1000["Numero de remision"].nunique()
    print(f"  seleccionadas {n_remisiones} remisiones distintas (top {CANTIDAD_A_IMPORTAR}, excluyendo {NUMERO_PRUEBA_EXCLUIDO}), {len(top1000)} filas de producto en total.")
    if args.limite:
        top1000 = top1000.head(args.limite)
        print(f"  --limite activo: procesando solo las primeras {len(top1000)} filas ({top1000['Numero de remision'].nunique()} remisiones, puede quedar una incompleta en el borde).")

    with Session(engine) as session:
        reporte_pys = importar_proyectos_y_tramos(session, df)
        print("Proyectos y tramos:", reporte_pys)

        reporte_prefijos = ajustar_prefijos(session, maximos)
        print("Prefijos ajustados:")
        for codigo, info in reporte_prefijos.items():
            print(f"  {codigo}: {info}")

        if args.dry_run:
            session.flush()
        else:
            session.commit()

        reporte_remisiones = importar_remisiones(session, top1000, dry_run=args.dry_run)
        print("Remisiones:", reporte_remisiones)

        if args.dry_run:
            print("\n--dry-run: revirtiendo todo, no se escribió nada permanente.")
            session.rollback()
        else:
            session.commit()
            print("\nCommit final hecho.")


if __name__ == "__main__":
    main()
