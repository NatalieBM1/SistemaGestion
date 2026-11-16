"""Lectura del Excel histórico (solo lectura, sin ejecutar macros).

Devuelve estructuras en memoria con el número de fila del Excel de cada
registro, para que el informe pueda citar filas y no datos personales.
"""

from __future__ import annotations

import warnings
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any

import openpyxl

from app.data_import import normalizar as N

COLUMNAS_REGISTROS = [
    "Numero de remision", "Fecha", "Forma de pago", "ODS", "ID del cliente", "Cliente", "Proyecto",
    "Tramo", "Origen", "Destino", "Kilometros", "Vehiculos", "Cama Baja", "Hora llegada",
    "Hora salida", "ID del conductor", "Conductor", "Tipo de transporte", "Observaciones",
    "Producto", "Cantidad", "Unidad de medida", "Valor Material", "Valor Flete",
    "Numero de viajes", "Valor de comision", "Valor de costo", "Valor cama baja",
    "Remision AGRESUR", "ID del usuario", "Usuario", "IngRegistro", "Factura", "Fecha Factura",
    "Tipo Facturacion", "Vr Facturado", "Vr Parcial Facturado", "Estado",
]

# Campos de cabecera: se toman de la primera línea de cada remisión y se
# comparan con las demás (las diferencias se reportan).
CAMPOS_CABECERA = [
    "fecha", "forma_pago", "ods", "cliente_id", "proyecto", "tramo", "origen", "destino",
    "kilometros", "vehiculo", "camabaja", "hora_llegada", "hora_salida", "conductor_id",
    "tipo_servicio", "observaciones", "remision_agresur", "usuario_id", "estado",
]


@dataclass
class Linea:
    fila: int
    prefijo: str
    consecutivo: int
    fecha: date | None
    forma_pago: str | None
    ods: str | None
    cliente_id: str | None
    cliente_nombre: str | None
    proyecto: str | None
    tramo: str | None
    origen: str | None
    destino: str | None
    kilometros: Decimal | None
    vehiculo: str | None
    camabaja: str | None
    hora_llegada: time | None
    hora_salida: time | None
    conductor_id: str | None
    conductor_nombre: str | None
    tipo_servicio: str | None
    observaciones: str | None
    producto: str | None
    cantidad: Decimal | None
    unidad: str | None
    valor_material: Decimal | None
    valor_flete: Decimal | None
    numero_viajes: int | None
    valor_comision: Decimal | None
    valor_costo: Decimal | None
    valor_camabaja: Decimal | None
    remision_agresur: str | None
    usuario_id: str | None
    usuario_nombre: str | None
    ing_registro: datetime | None
    factura: str | None
    fecha_factura: date | None
    tipo_facturacion: str | None
    vr_facturado: Decimal | None
    vr_parcial: Decimal | None
    estado: str | None
    estado_texto: str | None
    desplazada: bool = False
    horas_no_interpretadas: list[str] = field(default_factory=list)
    crudo: tuple = ()

    @property
    def numero(self) -> str:
        return f"{self.prefijo}-{self.consecutivo}"

    @property
    def valor_total(self) -> Decimal:
        return (self.valor_material or 0) + (self.valor_flete or 0) + (self.valor_camabaja or 0)


@dataclass
class Remision:
    prefijo: str
    consecutivo: int
    lineas: list[Linea]

    @property
    def numero(self) -> str:
        return f"{self.prefijo}-{self.consecutivo}"

    @property
    def cabecera(self) -> Linea:
        return self.lineas[0]


@dataclass
class Libro:
    lineas: list[Linea]
    remisiones: "OrderedDict[tuple[str, int], Remision]"
    filas_vacias: int
    filas_no_leidas: list[tuple[int, str]]
    terceros: list[dict[str, Any]]
    columnas_terceros: list[str]
    configuracion: dict[str, list[Any]]
    dane: list[dict[str, str]]
    empresa_nombre: str | None
    hojas: list[str]


def _encabezados(fila: tuple) -> dict[str, int]:
    return {N.clave(c): i for i, c in enumerate(fila) if c not in (None, "")}


def _leer_registros(ws) -> tuple[list[Linea], int, list[tuple[int, str]]]:
    filas = ws.iter_rows(values_only=True)
    enc = _encabezados(next(filas))
    faltan = [c for c in COLUMNAS_REGISTROS if N.clave(c) not in enc]
    if faltan:
        raise ValueError(f"La hoja Registros no tiene las columnas: {', '.join(faltan)}")
    idx = {c: enc[N.clave(c)] for c in COLUMNAS_REGISTROS}

    lineas: list[Linea] = []
    vacias = 0
    no_leidas: list[tuple[int, str]] = []
    for n, fila in enumerate(filas, start=2):
        valores = [fila[idx[c]] if idx[c] < len(fila) else None for c in COLUMNAS_REGISTROS]
        if all(v is None or (isinstance(v, str) and not v.strip()) for v in valores):
            vacias += 1
            continue
        v = dict(zip(COLUMNAS_REGISTROS, valores))
        clave_num = N.numero_remision(v["Numero de remision"])
        if clave_num is None:
            no_leidas.append((n, "número de remisión vacío o con formato no reconocido"))
            continue

        # Filas desplazadas (GIS, octubre 2026): Usuario vacío, Unidad = 0,
        # "ID del usuario" con el nombre y "Remision AGRESUR" con la cédula.
        desplazada = (
            v["Unidad de medida"] in (0, "0")
            and N.texto(v["Usuario"]) is None
            and isinstance(v["ID del usuario"], str)
            and not v["ID del usuario"].strip().isdigit()
            and N.texto(v["Remision AGRESUR"]) is not None
            and str(N.texto(v["Remision AGRESUR"])).isdigit()
        )
        if desplazada:
            usuario_nombre = N.texto(v["ID del usuario"])
            usuario_id = N.identificacion(v["Remision AGRESUR"])
            agresur = None
        else:
            usuario_nombre = N.texto(v["Usuario"])
            usuario_id = N.identificacion(v["ID del usuario"])
            agresur = N.texto(v["Remision AGRESUR"])

        horas_malas: list[str] = []
        hora_llegada, ok1 = N.hora(v["Hora llegada"])
        if not ok1:
            horas_malas.append("Hora llegada")
        hora_salida, ok2 = N.hora(v["Hora salida"])
        if not ok2:
            horas_malas.append("Hora salida")
        ing = v["IngRegistro"]

        lineas.append(
            Linea(
                fila=n,
                prefijo=clave_num[0],
                consecutivo=clave_num[1],
                fecha=N.fecha(v["Fecha"]),
                forma_pago=N.nombre_catalogo(v["Forma de pago"]),
                ods=N.texto(v["ODS"]),
                cliente_id=N.identificacion(v["ID del cliente"]),
                cliente_nombre=N.texto(v["Cliente"]),
                proyecto=N.texto(v["Proyecto"]),
                tramo=N.texto(v["Tramo"]),
                origen=N.texto(v["Origen"]),
                destino=N.texto(v["Destino"]),
                kilometros=N.decimal(v["Kilometros"]),
                vehiculo=N.nombre_catalogo(v["Vehiculos"]),
                camabaja=N.nombre_catalogo(v["Cama Baja"]),
                hora_llegada=hora_llegada,
                hora_salida=hora_salida,
                conductor_id=N.identificacion(v["ID del conductor"]),
                conductor_nombre=N.texto(v["Conductor"]),
                tipo_servicio=N.tipo_servicio(v["Tipo de transporte"]),
                observaciones=N.texto(v["Observaciones"]),
                producto=N.nombre_catalogo(v["Producto"]),
                cantidad=N.decimal(v["Cantidad"]),
                unidad=N.unidad(v["Unidad de medida"]),
                valor_material=N.decimal(v["Valor Material"]),
                valor_flete=N.decimal(v["Valor Flete"]),
                numero_viajes=N.entero(v["Numero de viajes"]),
                valor_comision=N.decimal(v["Valor de comision"]),
                valor_costo=N.decimal(v["Valor de costo"]),
                valor_camabaja=N.decimal(v["Valor cama baja"]),
                remision_agresur=agresur,
                usuario_id=usuario_id,
                usuario_nombre=usuario_nombre,
                ing_registro=ing if isinstance(ing, datetime) else None,
                factura=N.numero_factura(v["Factura"]),
                fecha_factura=N.fecha(v["Fecha Factura"]),
                tipo_facturacion=N.clave(v["Tipo Facturacion"]) or None,
                vr_facturado=N.decimal(v["Vr Facturado"]),
                vr_parcial=N.decimal(v["Vr Parcial Facturado"]),
                estado=N.estado(v["Estado"]),
                estado_texto=N.texto(v["Estado"]),
                desplazada=desplazada,
                horas_no_interpretadas=horas_malas,
                crudo=tuple(valores),
            )
        )
    return lineas, vacias, no_leidas


def _leer_terceros(ws) -> tuple[list[dict[str, Any]], list[str]]:
    filas = ws.iter_rows(values_only=True)
    encabezado = [N.texto(c) for c in next(filas)]
    columnas = [c for c in encabezado if c]
    terceros: list[dict[str, Any]] = []
    for n, fila in enumerate(filas, start=2):
        if not fila or all(c in (None, "") for c in fila):
            continue
        registro = {"_fila": n}
        for i, nombre in enumerate(encabezado):
            if nombre:
                registro[nombre] = fila[i] if i < len(fila) else None
        # Columnas sin encabezado con datos: se conservan con su letra.
        for i in range(len(encabezado), len(fila)):
            if fila[i] not in (None, ""):
                registro[f"columna_{i + 1}"] = fila[i]
        terceros.append(registro)
    return terceros, columnas


def _leer_configuracion(ws) -> dict[str, list[Any]]:
    filas = ws.iter_rows(values_only=True)
    encabezado = next(filas)
    columnas: dict[str, list[Any]] = defaultdict(list)
    for fila in filas:
        for i, nombre in enumerate(encabezado):
            if nombre and i < len(fila) and fila[i] not in (None, ""):
                columnas[N.clave(nombre)].append(fila[i])
    return dict(columnas)


def _leer_dane(ws) -> list[dict[str, str]]:
    filas = list(ws.iter_rows(values_only=True))
    inicio = next(i for i, f in enumerate(filas) if f and N.clave(f[0]).startswith("CODIGO DEPARTAMENTO"))
    salida = []
    for f in filas[inicio + 1:]:
        if not f or not f[1]:
            continue
        salida.append(
            {
                "codigo_departamento": str(f[0]).strip().zfill(2),
                "codigo_municipio": str(f[1]).strip().zfill(5),
                "codigo_centro": str(f[2]).strip() if f[2] else "",
                "departamento": N.texto(f[3]) or "",
                "municipio": N.texto(f[4]) or "",
                "centro": N.texto(f[5]) or "",
            }
        )
    return salida


def _leer_empresa(ws) -> str | None:
    for fila in ws.iter_rows(values_only=True):
        if fila and N.clave(fila[0]) == "NOMBRE EMPRESA":
            return N.texto(fila[1])
    return None


def leer(ruta: Path) -> Libro:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # avisos de extensiones de Excel no soportadas
        wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True, keep_vba=False)
    try:
        lineas, vacias, no_leidas = _leer_registros(wb["Registros"])
        terceros, columnas_terceros = _leer_terceros(wb["Terceros"])
        configuracion = _leer_configuracion(wb["Configuracion"])
        dane = _leer_dane(wb["DANE"])
        empresa = _leer_empresa(wb["Empresa"])
        hojas = list(wb.sheetnames)
    finally:
        wb.close()

    remisiones: OrderedDict[tuple[str, int], Remision] = OrderedDict()
    for linea in lineas:
        k = (linea.prefijo, linea.consecutivo)
        if k not in remisiones:
            remisiones[k] = Remision(linea.prefijo, linea.consecutivo, [])
        remisiones[k].lineas.append(linea)
    return Libro(
        lineas=lineas,
        remisiones=remisiones,
        filas_vacias=vacias,
        filas_no_leidas=no_leidas,
        terceros=terceros,
        columnas_terceros=columnas_terceros,
        configuracion=configuracion,
        dane=dane,
        empresa_nombre=empresa,
        hojas=hojas,
    )
