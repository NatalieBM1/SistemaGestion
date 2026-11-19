# ruff: noqa: DTZ001 — fechas de un Excel ficticio, sin zona horaria como el real
"""Importador del Excel histórico (app/data_import) con un libro FICTICIO.

Todos los datos son inventados (prefijo de prueba ZZT, clientes "CLIENTE
PRUEBA", placas ZZZ…). Las pruebas de base corren sobre el clon dentro de
una transacción que se revierte al final: no dejan nada guardado.
"""

from datetime import date, datetime, time
from decimal import Decimal

import openpyxl
import pytest
from fastapi import HTTPException
from sqlmodel import Session, select

from app.data_import import lector, validar
from app.data_import import normalizar as N
from app.data_import.carga import Carga
from app.models.catalogos import Prefijo
from app.models.facturacion import Factura, RemisionFacturacion
from app.models.remision import Remision, RemisionProducto
from app.models.usuario import Usuario
from app.services import facturacion_service

COLUMNAS = lector.COLUMNAS_REGISTROS


def _fila(**valores):
    base = {c: None for c in COLUMNAS}
    base.update(
        {
            "Fecha": datetime(2024, 3, 5),
            "Forma de pago": "CREDITO",
            "ID del cliente": 900000001,
            "Cliente": "CLIENTE PRUEBA UNO",
            "Origen": "Pasto - Nariño",
            "Destino": "PIEDRANCHA - NARIÑO",
            "Vehiculos": "ZZZ001",
            "ID del conductor": 800000001,
            "Conductor": "CONDUCTOR PRUEBA",
            "Tipo de transporte": "DESALOJOS",
            "Producto": "ARENA PRUEBA",
            "Cantidad": 8,
            "Unidad de medida": "METROS CUBICOS",
            "Valor Material": 0,
            "Valor Flete": 100000,
            "Numero de viajes": 2,
            "Valor de comision": 0,
            "Valor de costo": 0,
            "Valor cama baja": 0,
            "ID del usuario": 700000001,
            "Usuario": "Usuario Corto",
            "Estado": "NO FACTURADA",
        }
    )
    base.update(valores)
    return [base[c] for c in COLUMNAS]


def _libro(ruta):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Registros"
    ws.append(COLUMNAS)
    ws.append(_fila(**{"Numero de remision": "ZZT-1", "Hora salida": 0.4375, "Factura": "f-9-90001",
                       "Fecha Factura": datetime(2024, 3, 31), "Tipo Facturacion": "TOTAL", "Vr Facturado": 100000,
                       "Estado": "FACTURADA"}))
    # ZZT-2: dos líneas (una con producto vacío), "No aplica" con factura
    ws.append(_fila(**{"Numero de remision": "ZZT-000002", "Hora llegada": "6:00", "Factura": "F-9-90001",
                       "Fecha Factura": datetime(2024, 3, 31), "Tipo Facturacion": "TOTAL", "Vr Facturado": 100000,
                       "Estado": "NO APLICA FACTURACIÓN"}))
    ws.append(_fila(**{"Numero de remision": "ZZT-2", "Producto": None, "Cantidad": None, "Unidad de medida": None,
                       "Valor Flete": None, "Numero de viajes": None, "Estado": "NO APLICA FACTURACION"}))
    # ZZT-3: fila desplazada (Unidad = 0, Usuario vacío, nombre en ID del usuario, cédula en AGRESUR)
    ws.append(_fila(**{"Numero de remision": "ZZT-3", "Unidad de medida": 0, "Usuario": None,
                       "ID del usuario": "USUARIO DESPLAZADO", "Remision AGRESUR": 700000002,
                       "Valor Flete": -5000, "Hora salida": "texto raro"}))
    ws.append([None] * len(COLUMNAS))  # fila vacía: se ignora
    t = wb.create_sheet("Terceros")
    t.append(["CC o NIT", "RAZON SOCIAL o NOMBRES Y APELLIDOS", "DIRECCIÓN", "CIUDAD", "E-mail", "Telefono", "Regimen"])
    t.append([900000001, "CLIENTE PRUEBA UNO S.A.S.", "CALLE 1", "PASTO", "c@ejemplo.com", 3000000000, "COMUN"])
    t.append([800000001, "CONDUCTOR PRUEBA", None, None, None, None, None])
    t.append([700000001, "USUARIO PRUEBA NOMBRE COMPLETO", None, None, None, None, None])
    c = wb.create_sheet("Configuracion")
    c.append([None, "F PAGO", None, "U_medida", None, "PrefijoRemisiones"])
    c.append([None, "CONTADO", None, "UNIDADES", None, "ZZT"])
    d = wb.create_sheet("DANE")
    d.append(["DIVISION POLITICA DE COLOMBIA"])
    d.append(["Código Departamento", "Código Municipio", "Código Centro Poblado", "Nombre Departamento",
              "Nombre Municipio", "Nombre Centro Poblado", "DTO/MPIO/PUEBLO"])
    d.append(["52", "52435", "52435000", "NARIÑO", "MALLAMA", "PIEDRANCHA", "NARIÑO-MALLAMA-PIEDRANCHA"])
    e = wb.create_sheet("Empresa")
    e.append(["Información Empresa"])
    e.append(["Nombre Empresa", "EMPRESA PRUEBA S.A.S."])
    wb.save(ruta)
    return ruta


@pytest.fixture
def libro(tmp_path):
    return lector.leer(_libro(tmp_path / "ficticio.xlsx"))


@pytest.fixture
def session_con_rollback(pg_engine):
    conexion = pg_engine.connect()
    transaccion = conexion.begin()
    session = Session(bind=conexion, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaccion.rollback()
        conexion.close()


# ── Normalización (sin base) ──────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (time(6, 30, 15), (time(6, 30), True)),
        (datetime(2024, 1, 1, 14, 5), (time(14, 5), True)),
        (0.4375, (time(10, 30), True)),
        (45200.5, (time(12, 0), True)),
        ("6:00", (time(6, 0), True)),
        ("00:00:00", (time(0, 0), True)),
        (None, (None, True)),
        ("texto raro", (None, False)),
    ],
)
def test_hora(valor, esperado):
    assert N.hora(valor) == esperado


def test_reglas_de_normalizacion():
    assert N.numero_remision("GTS-006525") == N.numero_remision("GTS-6525") == ("GTS", 6525)
    assert N.numero_factura(" f-7-1780 ") == "F-7-1780"
    assert N.numero_factura("L-201-455") == "L-201-455"
    assert N.serie_factura("F-7-1780") == "F-7" and N.serie_factura("L-201-455") == "L-201"
    assert N.estado("NO APLICA FACTURACIÓN") == N.estado("No aplica facturacion") == "NO_APLICA"
    assert N.estado("FACTURADA PARCIALMENTE") == "FACTURADA_PARCIAL"
    assert N.tipo_servicio("DESALOJOS") == N.tipo_servicio("DESALOJO ") == "DESALOJO"
    assert N.tipo_servicio("MATERIA PRIMA ") == "MATERIA PRIMA"
    assert N.tipo_servicio("CAMABAJA") == "CAMABAJA"
    assert N.unidad("UNIDADES") == "UNIDAD"
    assert N.unidad("METROS CUBICOS") == "Metro cúbico"
    assert N.unidad(0) is None and N.unidad("0") is None
    assert N.identificacion(900123456) == "900123456"
    assert N.texto(12.0) == "12"


def test_lector_agrupa_y_realinea(libro):
    assert len(libro.lineas) == 4  # la fila vacía no cuenta
    assert len(libro.remisiones) == 3
    assert libro.filas_vacias == 1 and libro.filas_no_leidas == []
    zzt2 = libro.remisiones[("ZZT", 2)]
    assert [ln.fila for ln in zzt2.lineas] == [3, 4]
    desplazada = libro.remisiones[("ZZT", 3)].lineas[0]
    assert desplazada.desplazada
    assert desplazada.usuario_id == "700000002" and desplazada.usuario_nombre == "USUARIO DESPLAZADO"
    assert desplazada.remision_agresur is None and desplazada.unidad is None
    assert desplazada.horas_no_interpretadas == ["Hora salida"]
    primera = libro.remisiones[("ZZT", 1)].lineas[0]
    assert primera.hora_salida == time(10, 30) and primera.factura == "F-9-90001"


# ── Carga sobre el clon (todo se revierte) ───────────────────────────────────


def _cuenta(s, modelo):
    return len(s.exec(select(modelo.id)).all())


def test_simulacion_no_escribe(session_con_rollback, libro):
    s = session_con_rollback
    antes = (_cuenta(s, Remision), _cuenta(s, RemisionProducto), _cuenta(s, Factura), _cuenta(s, Usuario))
    r = Carga(s, libro, simulacion=True).ejecutar()
    s.rollback()
    assert r.creados["remisiones"] == 3 and r.lineas_cargadas == 4
    assert (_cuenta(s, Remision), _cuenta(s, RemisionProducto), _cuenta(s, Factura), _cuenta(s, Usuario)) == antes


def test_carga_completa_e_idempotente(session_con_rollback, libro):
    s = session_con_rollback
    r = Carga(s, libro, simulacion=False).ejecutar()
    assert r.fallidas == []
    assert r.creados["remisiones"] == 3 and r.lineas_cargadas == 4 and r.creados["facturas"] == 1

    rems = {x.numero_remision: x for x in s.exec(select(Remision).where(Remision.numero_remision.like("ZZT-%"))).all()}
    assert set(rems) == {"ZZT-1", "ZZT-2", "ZZT-3"}
    assert rems["ZZT-2"].estado_facturacion == "NO_APLICA"
    assert rems["ZZT-1"].hora_salida == time(10, 30)
    # Línea sin producto ni cantidad ni viajes: queda vacía (no se inventa).
    lineas_2 = s.exec(select(RemisionProducto).where(RemisionProducto.remision_id == rems["ZZT-2"].id)).all()
    assert sorted((ln.producto_id is None, ln.cantidad is None, ln.numero_viajes is None) for ln in lineas_2) == [
        (False, False, False),
        (True, True, True),
    ]
    # Negativo tal cual.
    linea_3 = s.exec(select(RemisionProducto).where(RemisionProducto.remision_id == rems["ZZT-3"].id)).one()
    assert linea_3.valor_flete == Decimal("-5000") and linea_3.unidad_medida_id is None
    # Factura normalizada a mayúsculas, con las dos remisiones (una "No aplica").
    factura = s.exec(select(Factura).where(Factura.numero_factura == "F-9-90001")).one()
    assert factura.fecha_factura == date(2024, 3, 31)
    assert len(s.exec(select(RemisionFacturacion).where(RemisionFacturacion.factura_id == factura.id)).all()) == 2
    # Usuarios históricos: sin acceso, con su cédula; el desplazado realineado.
    creador = s.get(Usuario, rems["ZZT-3"].usuario_creador_id)
    assert creador.identificacion == "700000002" and creador.historico and not creador.activo
    assert creador.email is None and creador.password_hash is None
    assert s.get(Usuario, rems["ZZT-1"].usuario_creador_id).nombre == "USUARIO PRUEBA NOMBRE COMPLETO"
    # Consecutivo: la próxima remisión automática toma máximo + 1.
    assert s.exec(select(Prefijo).where(Prefijo.codigo == "ZZT")).one().consecutivo_actual == 3

    # Validación contra la base: cuadra.
    est_excel = validar.estadisticas_excel(libro)
    est_bd = validar.estadisticas_bd(s, libro)
    for clave in ("registros", "remisiones", "facturas", "clientes", "conductores", "placas", "productos"):
        assert est_excel[clave] == est_bd[clave], clave

    # Segunda corrida: no cambia nada.
    r2 = Carga(s, libro, simulacion=False).ejecutar()
    assert r2.creados["remisiones"] == 0 and r2.remisiones_omitidas == 3 and r2.lineas_omitidas_por_existir == 4


def test_no_aplica_no_se_factura_y_conserva_su_estado(session_con_rollback, libro):
    s = session_con_rollback
    Carga(s, libro, simulacion=False).ejecutar()
    rem = s.exec(select(Remision).where(Remision.numero_remision == "ZZT-2")).one()
    with pytest.raises(HTTPException) as exc:
        facturacion_service.facturar_remision(
            s, remision=rem, numero_factura="F-9-90002", fecha_factura=date(2024, 4, 1),
            tipo="TOTAL", valor_facturado_input=None, usuario_id=None,
        )
    assert exc.value.status_code == 400 and "No aplica" in exc.value.detail
    assert facturacion_service.recalcular_estado_facturacion(s, rem.id) == "NO_APLICA"
    _, errores, _ = facturacion_service._validar_seleccion_para_facturar_multiple(s, [rem.id])
    assert errores and "No aplica" in errores[0]["motivo"]
