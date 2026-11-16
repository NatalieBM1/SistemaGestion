"""Escritura de la carga histórica en la base (Bloque 1).

Etapas, en orden: catálogos → ubicaciones DANE → terceros → vehículos y cama
baja → usuarios históricos → proyectos, tramos y ODS → remisiones con sus
líneas y su facturación.

- Idempotente: cada entidad se busca por su clave natural antes de crearla;
  una remisión que ya existe (mismo prefijo y consecutivo numérico, con o sin
  ceros a la izquierda) se omite.
- Lotes de N remisiones por transacción: o entra la remisión completa (con
  sus líneas y su facturación) o no entra nada de ella. Si se interrumpe, se
  vuelve a correr y continúa donde quedó.
- Modo simulación: no escribe nada; usa ids provisionales y deja el plan en
  el informe.
"""

from __future__ import annotations

import sys
import time as reloj
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import openpyxl
from sqlmodel import Session, select

from app.core import numero_remision as numero_remision_svc
from app.data_import import normalizar as N
from app.data_import.lector import CAMPOS_CABECERA, Libro, Linea, Remision as RemisionExcel
from app.models.activo import Activo, EmpresaGrupo
from app.models.catalogos import (
    FormaPago,
    Prefijo,
    PrefijoFactura,
    Producto,
    Proyecto,
    TipoServicio,
    Tramo,
    UnidadMedida,
)
from app.models.facturacion import Factura, RemisionFacturacion
from app.models.orden_servicio import OrdenServicio
from app.models.remision import Remision, RemisionProducto
from app.models.tercero import Tercero, TerceroTipo, TipoTercero
from app.models.ubicacion import Departamento, Municipio
from app.models.usuario import Usuario

RUTA_DANE_NACIONAL = (
    Path(__file__).resolve().parent
    / "formatos"
    / "Listado-censal-consejos-organizaciones-base-formas-y-expr.-organizativas.-Anexo-3.-Vr-02-25-02-2022.xlsx"
)

PREFIJOS_AUTOMATICOS = ["GTS", "GIS", "GI", "PUT", "AJUSTE", "AE", "GT", "GTC", "GTI", "NC"]
PREFIJOS_MANUALES = ["GTM"]
ALIAS_MUNICIPIO = {"SAN JUAN DE PASTO": "PASTO"}
SIN_ESPECIFICAR = "00000"


@dataclass
class Resultado:
    """Todo lo que el informe necesita contar (sin datos personales)."""

    creados: Counter = field(default_factory=Counter)
    existentes: Counter = field(default_factory=Counter)
    remisiones_nuevas: list[str] = field(default_factory=list)
    remisiones_omitidas: int = 0
    lineas_cargadas: int = 0
    lineas_omitidas_por_existir: int = 0
    lineas_fuera_de_rango: int = 0
    remisiones_fuera_de_rango: int = 0
    facturaciones: int = 0
    fallidas: list[tuple[str, list[int], str]] = field(default_factory=list)
    ubicaciones_no_resueltas: Counter = field(default_factory=Counter)
    ubicaciones_resueltas_por_centro: dict[str, str] = field(default_factory=dict)
    terceros_ciudad: Counter = field(default_factory=Counter)
    prefijos: dict[str, tuple[int, int, int]] = field(default_factory=dict)
    ods_varios_clientes: list[str] = field(default_factory=list)
    duracion: dict[str, float] = field(default_factory=dict)


class Carga:
    def __init__(self, session: Session, libro: Libro, *, simulacion: bool, lote: int = 500, desde: date | None = None):
        self.s = session
        self.libro = libro
        self.sim = simulacion
        self.lote = lote
        self.desde = desde
        self.r = Resultado()
        self._id_provisional = 0

    # ── utilidades ────────────────────────────────────────────────────────
    def _nuevo(self, obj, tipo: str):
        """Crea `obj` (o le da un id provisional en simulación)."""
        self.r.creados[tipo] += 1
        if self.sim:
            self._id_provisional -= 1
            obj.id = self._id_provisional
        else:
            self.s.add(obj)
            self.s.flush()
        return obj

    def _commit(self):
        if not self.sim:
            self.s.commit()

    def _por_clave(self, modelo, campo: str) -> dict[str, Any]:
        return {N.clave(getattr(o, campo)): o for o in self.s.exec(select(modelo)).all()}

    def _catalogo(self, cache: dict, modelo, valor: str | None, tipo: str, **extra):
        if not valor:
            return None
        k = N.clave(valor)
        if k not in cache:
            cache[k] = self._nuevo(modelo(nombre=valor, **extra), tipo)
        return cache[k]

    def _progreso(self, hechas: int, total: int, inicio: float):
        ancho = 30
        lleno = int(ancho * hechas / total) if total else ancho
        seg = reloj.monotonic() - inicio
        sys.stderr.write(f"\r  [{'#' * lleno}{'.' * (ancho - lleno)}] {hechas:>6}/{total} remisiones  {seg:6.1f} s")
        sys.stderr.flush()

    # ── etapas ────────────────────────────────────────────────────────────
    def catalogos(self):
        L, cfg = self.libro, self.libro.configuracion
        self.formas = self._por_clave(FormaPago, "nombre")
        for v in cfg.get("F PAGO", []) + [l.forma_pago for l in L.lineas]:
            self._catalogo(self.formas, FormaPago, N.nombre_catalogo(v), "formas_pago")

        self.tipos = self._por_clave(TipoServicio, "nombre")
        for v in cfg.get("DETALLE1", []) + [l.tipo_servicio for l in L.lineas]:
            self._catalogo(self.tipos, TipoServicio, N.tipo_servicio(v), "tipos_servicio")

        self.unidades = self._por_clave(UnidadMedida, "nombre")
        for v in cfg.get("U_MEDIDA", []) + [l.unidad for l in L.lineas]:
            self._catalogo(self.unidades, UnidadMedida, N.unidad(v), "unidades_medida")

        self.productos = self._por_clave(Producto, "nombre")
        for v in cfg.get("DETALLE2", []) + [l.producto for l in L.lineas]:
            self._catalogo(self.productos, Producto, N.nombre_catalogo(v), "productos")

        self.prefijos = self._por_clave(Prefijo, "codigo")
        codigos = [N.nombre_catalogo(p) for p in cfg.get("PREFIJOREMISIONES", [])]
        codigos += PREFIJOS_AUTOMATICOS + PREFIJOS_MANUALES + [l.prefijo for l in L.lineas]
        for codigo in dict.fromkeys(c for c in codigos if c):
            if N.clave(codigo) not in self.prefijos:
                self.prefijos[N.clave(codigo)] = self._nuevo(
                    Prefijo(codigo=codigo, consecutivo_actual=0, es_manual=codigo in PREFIJOS_MANUALES), "prefijos"
                )

        self.prefijos_factura = self._por_clave(PrefijoFactura, "codigo")
        series = [N.nombre_catalogo(p) for p in cfg.get("PREFIJOFACTURAS", [])]
        series += [N.serie_factura(l.factura) for l in L.lineas if l.factura]
        for codigo in dict.fromkeys(c for c in series if c):
            if N.clave(codigo) not in self.prefijos_factura:
                self.prefijos_factura[N.clave(codigo)] = self._nuevo(PrefijoFactura(codigo=codigo), "prefijos_factura")

        self.tipos_tercero = self._por_clave(TipoTercero, "nombre")
        for nombre in ("CLIENTE", "CONDUCTOR"):
            self._catalogo(self.tipos_tercero, TipoTercero, nombre, "tipos_tercero")

        self.empresas = self._por_clave(EmpresaGrupo, "nombre")
        if L.empresa_nombre:
            self._catalogo(self.empresas, EmpresaGrupo, L.empresa_nombre, "empresas_grupo")
        self._commit()

    def ubicaciones(self):
        deptos = {d.codigo_dane: d for d in self.s.exec(select(Departamento)).all()}
        munis = {m.codigo_dane: m for m in self.s.exec(select(Municipio)).all()}

        nacional_deptos: dict[str, str] = {}
        nacional_munis: list[tuple[str, str]] = []
        if RUTA_DANE_NACIONAL.exists():
            wb = openpyxl.load_workbook(RUTA_DANE_NACIONAL, read_only=True, data_only=True)
            hoja_d = next(n for n in wb.sheetnames if "Departamentos" in n)
            for f in list(wb[hoja_d].iter_rows(values_only=True))[1:]:
                if f and f[0] is not None and f[1]:
                    nacional_deptos[str(f[0]).strip().zfill(2)] = str(f[1]).strip()
            for f in list(wb["Municipios"].iter_rows(values_only=True))[1:]:
                if f and f[0] and f[1]:
                    nacional_munis.append((str(f[0]).strip().zfill(5), str(f[1]).strip()))
            wb.close()
        for d in self.libro.dane:
            nacional_deptos.setdefault(d["codigo_departamento"], d["departamento"])
        nombres_munis = dict(nacional_munis)
        for d in self.libro.dane:
            nombres_munis.setdefault(d["codigo_municipio"], d["municipio"])

        for codigo, nombre in sorted(nacional_deptos.items()):
            if codigo not in deptos:
                deptos[codigo] = self._nuevo(Departamento(codigo_dane=codigo, nombre=nombre.upper()), "departamentos")
        for codigo, nombre in sorted(nombres_munis.items()):
            if codigo not in munis and codigo[:2] in deptos:
                munis[codigo] = self._nuevo(
                    Municipio(codigo_dane=codigo, nombre=nombre.upper(), departamento_id=deptos[codigo[:2]].id),
                    "municipios",
                )
        self._commit()

        # Índices para resolver "Municipio - Departamento".
        depto_de = {c: N.clave(d.nombre) for c, d in deptos.items()}
        self._muni_por_nombre_depto: dict[tuple[str, str], Municipio] = {}
        self._muni_por_nombre: dict[str, list[Municipio]] = defaultdict(list)
        for codigo, m in munis.items():
            dn = depto_de.get(codigo[:2], "")
            self._muni_por_nombre_depto[(N.clave(m.nombre), dn)] = m
            self._muni_por_nombre[N.clave(m.nombre)].append(m)
        self._centros: dict[tuple[str, str], str] = {}
        for d in self.libro.dane:
            self._centros[(N.clave(d["centro"]), N.clave(d["departamento"]))] = d["codigo_municipio"]
        self._munis = munis
        self._deptos = deptos
        self._cache_ubicacion: dict[str, Municipio | None] = {}

    def _depto_comparable(self, texto: str) -> str:
        return N.clave(texto).replace(",", "").replace(".", "").replace(" DC", "").strip()

    def municipio(self, texto: str | None) -> Municipio | None:
        if not texto:
            return None
        if texto in self._cache_ubicacion:
            return self._cache_ubicacion[texto]
        partes = texto.rsplit(" - ", 1)
        nombre = N.clave(partes[0])
        depto = self._depto_comparable(partes[1]) if len(partes) > 1 else ""
        candidatos = [nombre, ALIAS_MUNICIPIO.get(nombre, nombre)]
        if "(" in nombre:
            base, _, resto = nombre.partition("(")
            candidatos += [base.strip(), resto.rstrip(")").strip()]
        encontrado = None
        for c in candidatos:
            for (n, d), m in self._muni_por_nombre_depto.items():
                if n == c and (not depto or self._depto_comparable(d) == depto):
                    encontrado = m
                    break
            if encontrado:
                break
        if encontrado is None:
            for c in candidatos:
                for (centro, d), codigo in self._centros.items():
                    if centro == c and (not depto or self._depto_comparable(d) == depto) and codigo in self._munis:
                        encontrado = self._munis[codigo]
                        self.r.ubicaciones_resueltas_por_centro[texto] = encontrado.nombre
                        break
                if encontrado:
                    break
        self._cache_ubicacion[texto] = encontrado
        return encontrado

    def _sin_especificar(self) -> Municipio:
        if SIN_ESPECIFICAR not in self._munis:
            depto = self._deptos.get("00") or self._nuevo(Departamento(codigo_dane="00", nombre="SIN ESPECIFICAR"), "departamentos")
            self._deptos["00"] = depto
            self._munis[SIN_ESPECIFICAR] = self._nuevo(
                Municipio(codigo_dane=SIN_ESPECIFICAR, nombre="SIN ESPECIFICAR", departamento_id=depto.id), "municipios"
            )
        return self._munis[SIN_ESPECIFICAR]

    def terceros(self):
        self.terc = {t.identificacion: t for t in self.s.exec(select(Tercero)).all()}
        cols = self.libro.columnas_terceros
        col_id, col_nombre, col_dir, col_ciudad, col_email, col_tel, col_reg = cols[:7]
        for fila in self.libro.terceros:
            ident = N.identificacion(fila.get(col_id))
            if not ident:
                continue
            if ident in self.terc:
                self.r.existentes["terceros"] += 1
                continue
            ciudad = N.texto(fila.get(col_ciudad))
            municipio_id = None
            if ciudad:
                opciones = self._muni_por_nombre.get(N.clave(ciudad), [])
                if len(opciones) == 1:
                    municipio_id = opciones[0].id
                    self.r.terceros_ciudad["municipio identificado"] += 1
                elif opciones:
                    self.r.terceros_ciudad["nombre de municipio repetido en varios departamentos (queda solo el texto)"] += 1
                else:
                    self.r.terceros_ciudad["no coincide con un municipio DANE (queda solo el texto)"] += 1
            self.terc[ident] = self._nuevo(
                Tercero(
                    identificacion=ident,
                    nombre=N.texto(fila.get(col_nombre)) or ident,
                    direccion=N.texto(fila.get(col_dir)),
                    ciudad=ciudad,
                    municipio_id=municipio_id,
                    email=N.texto(fila.get(col_email)),
                    telefono=N.texto(fila.get(col_tel)),
                    regimen=N.texto(fila.get(col_reg)),
                ),
                "terceros",
            )
        # Clientes y conductores que no estén en la hoja Terceros.
        for l in self.libro.lineas:
            for ident, nombre in ((l.cliente_id, l.cliente_nombre), (l.conductor_id, l.conductor_nombre)):
                if ident and ident not in self.terc:
                    self.terc[ident] = self._nuevo(Tercero(identificacion=ident, nombre=nombre or ident), "terceros_desde_registros")
        # Tipos CLIENTE / CONDUCTOR.
        existentes = {(tt.tercero_id, tt.tipo_id) for tt in self.s.exec(select(TerceroTipo)).all()}
        tipo_cli = self.tipos_tercero["CLIENTE"]
        tipo_con = self.tipos_tercero["CONDUCTOR"]
        pares = {(self.terc[l.cliente_id].id, tipo_cli.id) for l in self.libro.lineas if l.cliente_id}
        pares |= {(self.terc[l.conductor_id].id, tipo_con.id) for l in self.libro.lineas if l.conductor_id}
        for tercero_id, tipo_id in sorted(pares - existentes):
            self.r.creados["tercero_tipos"] += 1
            if not self.sim:
                self.s.add(TerceroTipo(tercero_id=tercero_id, tipo_id=tipo_id))
        self._commit()

    def activos(self):
        self.act = {N.clave(a.placa): a for a in self.s.exec(select(Activo)).all()}
        cfg = self.libro.configuracion
        vehiculos = [N.nombre_catalogo(p) for p in cfg.get("VEHICULOS", [])] + [l.vehiculo for l in self.libro.lineas]
        camabajas = [N.nombre_catalogo(p) for p in cfg.get("CAMABAJAS", [])] + [l.camabaja for l in self.libro.lineas]
        for placas, tipo in ((camabajas, "CAMA BAJA"), (vehiculos, "VEHÍCULO")):
            for placa in dict.fromkeys(p for p in placas if p):
                if N.clave(placa) not in self.act:
                    self.act[N.clave(placa)] = self._nuevo(Activo(placa=placa, tipo_activo=tipo), "activos")
        self._commit()

    def usuarios(self):
        existentes = [u for u in self.s.exec(select(Usuario)).all() if u.identificacion]
        self.usu = {u.identificacion: u for u in existentes}
        nombres_terceros = {N.identificacion(f.get(self.libro.columnas_terceros[0])): N.texto(f.get(self.libro.columnas_terceros[1])) for f in self.libro.terceros}
        por_id: dict[str, Counter] = defaultdict(Counter)
        for l in self.libro.lineas:
            if l.usuario_id:
                por_id[l.usuario_id][l.usuario_nombre or ""] += 1
        for ident, nombres in por_id.items():
            if ident in self.usu:
                self.r.existentes["usuarios_historicos"] += 1
                continue
            nombre = nombres_terceros.get(ident) or max(nombres, key=lambda n: (len(n), nombres[n])) or ident
            self.usu[ident] = self._nuevo(
                Usuario(nombre=nombre, email=None, password_hash=None, identificacion=ident, activo=False, historico=True),
                "usuarios_historicos",
            )
        self._commit()

    def proyectos_y_ods(self):
        self.proy = {(N.clave(p.nombre), p.cliente_id): p for p in self.s.exec(select(Proyecto)).all()}
        self.tram = {(t.proyecto_id, N.clave(t.nombre)): t for t in self.s.exec(select(Tramo)).all()}
        self.ods = {N.clave(o.numero): o for o in self.s.exec(select(OrdenServicio)).all()}
        clientes_ods: dict[str, set] = defaultdict(set)
        for l in self.libro.lineas:
            cliente = self.terc[l.cliente_id]
            if l.proyecto:
                k = (N.clave(l.proyecto), cliente.id)
                if k not in self.proy:
                    self.proy[k] = self._nuevo(Proyecto(nombre=l.proyecto, cliente_id=cliente.id), "proyectos")
                if l.tramo:
                    kt = (self.proy[k].id, N.clave(l.tramo))
                    if kt not in self.tram:
                        self.tram[kt] = self._nuevo(Tramo(proyecto_id=self.proy[k].id, nombre=l.tramo), "tramos")
            if l.ods:
                clientes_ods[N.clave(l.ods)].add(cliente.id)
                if N.clave(l.ods) not in self.ods:
                    self.ods[N.clave(l.ods)] = self._nuevo(
                        OrdenServicio(numero=l.ods, cliente_id=cliente.id, valor_tope=None, saldo_disponible=None),
                        "ordenes_servicio",
                    )
        self.r.ods_varios_clientes = sorted(k for k, v in clientes_ods.items() if len(v) > 1)
        self._commit()

    # ── remisiones ────────────────────────────────────────────────────────
    def _existentes(self) -> set[tuple[str, int]]:
        claves = set()
        for numero in self.s.exec(select(Remision.numero_remision)).all():
            c = numero_remision_svc.clave(numero)
            if c:
                claves.add(c)
        return claves

    def _armar(self, rem: RemisionExcel) -> tuple[Remision, list[RemisionProducto], list[tuple[str, date | None, str, Decimal]]]:
        c = rem.cabecera
        cliente = self.terc[c.cliente_id]
        proyecto = self.proy.get((N.clave(c.proyecto), cliente.id)) if c.proyecto else None
        tramo = self.tram.get((proyecto.id, N.clave(c.tramo))) if proyecto and c.tramo else None
        origen = self.municipio(c.origen)
        destino = self.municipio(c.destino)
        for texto_ubicacion, resuelto in ((c.origen, origen), (c.destino, destino)):
            if resuelto is None:
                self.r.ubicaciones_no_resueltas[texto_ubicacion or "(vacío)"] += 1
        origen = origen or self._sin_especificar()
        destino = destino or self._sin_especificar()
        usuario = self.usu.get(c.usuario_id) if c.usuario_id else None
        if usuario is None:
            raise ValueError("sin usuario creador identificable")
        remision = Remision(
            numero_remision=rem.numero,
            prefijo_id=self.prefijos[N.clave(rem.prefijo)].id,
            consecutivo=str(rem.consecutivo),
            orden_servicio_id=self.ods[N.clave(c.ods)].id if c.ods else None,
            fecha=c.fecha,
            forma_pago_id=self.formas[N.clave(c.forma_pago)].id if c.forma_pago else None,
            cliente_id=cliente.id,
            conductor_id=self.terc[c.conductor_id].id if c.conductor_id else None,
            origen_municipio_id=origen.id,
            destino_municipio_id=destino.id,
            proyecto_id=proyecto.id if proyecto else None,
            tramo_id=tramo.id if tramo else None,
            tipo_servicio_id=self.tipos[N.clave(c.tipo_servicio)].id if c.tipo_servicio else None,
            vehiculo_id=self.act[N.clave(c.vehiculo)].id if c.vehiculo else None,
            camabaja_id=self.act[N.clave(c.camabaja)].id if c.camabaja else None,
            kilometros=c.kilometros,
            hora_salida=c.hora_salida,
            hora_llegada=c.hora_llegada,
            remision_agresur=c.remision_agresur,
            observaciones=c.observaciones,
            usuario_creador_id=usuario.id,
            estado_facturacion=c.estado or "NO_FACTURADA",
            ing_registro=c.ing_registro,
        )
        productos = [
            RemisionProducto(
                remision_id=0,
                producto_id=self.productos[N.clave(l.producto)].id if l.producto else None,
                cantidad=l.cantidad,
                unidad_medida_id=self.unidades[N.clave(l.unidad)].id if l.unidad else None,
                valor_material=l.valor_material or Decimal(0),
                valor_flete=l.valor_flete or Decimal(0),
                valor_camabaja=l.valor_camabaja or Decimal(0),
                numero_viajes=l.numero_viajes,
                valor_comision=l.valor_comision or Decimal(0),
                valor_costo=l.valor_costo or Decimal(0),
            )
            for l in rem.lineas
        ]
        # Facturación: una por (remisión, factura), sumando Vr Facturado de
        # sus líneas (Vr Facturado viene por línea). PARCIAL si alguna línea
        # lo dice; si viene Vr Parcial Facturado se usa ese valor.
        por_factura: dict[str, list[Linea]] = defaultdict(list)
        for l in rem.lineas:
            if l.factura:
                por_factura[l.factura].append(l)
        facturaciones = []
        for numero, lineas in por_factura.items():
            tipo = "PARCIAL" if any(l.tipo_facturacion == "PARCIAL" for l in lineas) else "TOTAL"
            valor = sum(((l.vr_parcial if l.vr_parcial is not None else l.vr_facturado) or Decimal(0) for l in lineas), Decimal(0))
            facturaciones.append((numero, lineas[0].fecha_factura, tipo, valor))
        return remision, productos, facturaciones

    def remisiones(self):
        inicio = reloj.monotonic()
        existentes = self._existentes()
        self.fact = {f.numero_factura: f for f in self.s.exec(select(Factura)).all()}
        pendientes: list[RemisionExcel] = []
        for k, rem in self.libro.remisiones.items():
            if self.desde and rem.cabecera.fecha and rem.cabecera.fecha < self.desde:
                self.r.remisiones_fuera_de_rango += 1
                self.r.lineas_fuera_de_rango += len(rem.lineas)
                continue
            if k in existentes:
                self.r.remisiones_omitidas += 1
                self.r.lineas_omitidas_por_existir += len(rem.lineas)
                continue
            pendientes.append(rem)

        total = len(pendientes)
        for i in range(0, total, self.lote):
            bloque = pendientes[i : i + self.lote]
            try:
                armadas = [(rem, *self._armar(rem)) for rem in bloque]
                if not self.sim:
                    for _, remision, _, _ in armadas:
                        self.s.add(remision)
                    self.s.flush()
                    for rem, remision, productos, facturaciones in armadas:
                        for p in productos:
                            p.remision_id = remision.id
                            self.s.add(p)
                        for numero, fecha_factura, tipo, valor in facturaciones:
                            factura = self.fact.get(numero)
                            if factura is None:
                                factura = Factura(numero_factura=numero, fecha_factura=fecha_factura)
                                self.s.add(factura)
                                self.s.flush()
                                self.fact[numero] = factura
                                self.r.creados["facturas"] += 1
                            self.s.add(
                                RemisionFacturacion(
                                    remision_id=remision.id,
                                    factura_id=factura.id,
                                    tipo_facturacion=tipo,
                                    valor_facturado=valor,
                                    usuario_id=remision.usuario_creador_id,
                                )
                            )
                    self.s.commit()
                else:
                    for _, _, _, facturaciones in armadas:
                        for numero, *_ in facturaciones:
                            if numero not in self.fact:
                                self.fact[numero] = None
                                self.r.creados["facturas"] += 1
                for rem, _, productos, facturaciones in armadas:
                    self.r.remisiones_nuevas.append(rem.numero)
                    self.r.lineas_cargadas += len(productos)
                    self.r.facturaciones += len(facturaciones)
                self.r.creados["remisiones"] += len(armadas)
                self.r.creados["remision_productos"] += sum(len(a[2]) for a in armadas)
            except Exception as exc:  # el lote entero queda fuera; se reporta
                if not self.sim:
                    self.s.rollback()
                    self.fact = {f.numero_factura: f for f in self.s.exec(select(Factura)).all()}
                for rem in bloque:
                    self.r.fallidas.append((rem.numero, [l.fila for l in rem.lineas], f"{type(exc).__name__}: {str(exc)[:200]}"))
            self._progreso(min(i + self.lote, total), total, inicio)
        if total:
            sys.stderr.write("\n")

    def consecutivos(self):
        """consecutivo_actual = último número usado (máximo del Excel), así la
        siguiente remisión automática toma máximo + 1. Nunca se baja."""
        maximos: dict[str, int] = defaultdict(int)
        for p, n in self.libro.remisiones:
            maximos[p] = max(maximos[p], n)
        for codigo, maximo in sorted(maximos.items()):
            pref = self.prefijos[N.clave(codigo)]
            antes = pref.consecutivo_actual or 0
            nuevo = max(antes, maximo)
            self.r.prefijos[codigo] = (antes, nuevo, maximo)
            if nuevo != antes and not self.sim:
                pref.consecutivo_actual = nuevo
                self.s.add(pref)
        self._commit()

    def ejecutar(self) -> Resultado:
        for nombre, etapa in (
            ("catálogos", self.catalogos),
            ("ubicaciones DANE", self.ubicaciones),
            ("terceros", self.terceros),
            ("vehículos y cama baja", self.activos),
            ("usuarios históricos", self.usuarios),
            ("proyectos, tramos y ODS", self.proyectos_y_ods),
            ("remisiones, líneas y facturación", self.remisiones),
            ("consecutivos de prefijos", self.consecutivos),
        ):
            t0 = reloj.monotonic()
            sys.stderr.write(f"- {nombre}...\n")
            etapa()
            self.r.duracion[nombre] = reloj.monotonic() - t0
        return self.r
