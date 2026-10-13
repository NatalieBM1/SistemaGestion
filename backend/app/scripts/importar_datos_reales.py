"""Importa datos reales del cliente desde el Excel histórico
(backend/app/data_import/RemisionesTG&G.xlsm) hacia las tablas base:
departamentos/municipios (hoja DANE), terceros (hoja Terceros), catálogos y
activos (hoja Configuracion) y empresas_grupo (hoja Empresa).

NO carga la hoja "Registros" (remisiones históricas, ~17.615 filas) — eso
queda para una fase de migración separada.

Idempotente: se puede correr varias veces sin duplicar (get_or_create por
campo único en cada entidad).

Uso:
    python -m app.scripts.importar_datos_reales --preview   (no toca la BD)
    python -m app.scripts.importar_datos_reales --aplicar   (inserta de verdad)
"""

import argparse
import csv
import sys
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd
from sqlmodel import Session, select

# En Windows, stdout redirigido a archivo/pipe usa el codepage ANSI del
# sistema por defecto (no UTF-8), lo que corrompe nombres con tildes/Ñ en la
# salida de este script (departamentos, ciudades, razones sociales).
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import engine
from app.models.activo import Activo, EmpresaGrupo
from app.models.catalogos import (
    FormaPago,
    Prefijo,
    PrefijoFactura,
    Producto,
    TipoServicio,
    UnidadMedida,
)
from app.models.tercero import Tercero
from app.models.ubicacion import Departamento, Municipio

RUTA_EXCEL = Path(__file__).resolve().parents[1] / "data_import" / "RemisionesTG&G.xlsm"
RUTA_REPORTE_SIN_MUNICIPIO = (
    Path(__file__).resolve().parents[1] / "data_import" / "terceros_sin_municipio.csv"
)

DEPARTAMENTO_FALLBACK_CODIGO = "00"
MUNICIPIO_FALLBACK_CODIGO = "00000"


def _normalizar(texto: Any) -> str:
    texto = str(texto).strip().upper()
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def _texto_o_defecto(valor: Any, defecto: str) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return defecto
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    texto = str(valor).strip()
    return texto if texto and texto.lower() != "nan" else defecto


def _obtener_o_crear(session: Session, model, *, defaults: dict | None = None, **filtros):
    statement = select(model)
    for campo, valor in filtros.items():
        statement = statement.where(getattr(model, campo) == valor)
    obj = session.exec(statement).first()
    if obj is not None:
        return obj
    obj = model(**filtros, **(defaults or {}))
    session.add(obj)
    session.flush()
    return obj


def _valores_unicos_columna(df: pd.DataFrame, columna: str) -> list[str]:
    if columna not in df.columns:
        return []
    valores = []
    for v in df[columna].dropna().tolist():
        texto = str(v).strip()
        if texto and texto.lower() != "nan":
            valores.append(texto)
    return valores


# --- DANE: departamentos y municipios ---


def _leer_dane(ruta: Path) -> pd.DataFrame:
    df = pd.read_excel(ruta, sheet_name="DANE", header=1)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def cargar_dane(session: Session, ruta: Path) -> dict[str, Any]:
    df = _leer_dane(ruta)
    deptos_unicos = df[["Código Departamento", "Nombre Departamento"]].drop_duplicates()
    creados_depto = 0
    departamentos_por_codigo: dict[str, Departamento] = {}
    for _, fila in deptos_unicos.iterrows():
        codigo = str(int(fila["Código Departamento"])).zfill(2)
        antes = session.exec(select(Departamento).where(Departamento.codigo_dane == codigo)).first()
        depto = _obtener_o_crear(
            session, Departamento, codigo_dane=codigo,
            defaults={"nombre": str(fila["Nombre Departamento"]).strip()},
        )
        departamentos_por_codigo[codigo] = depto
        if antes is None:
            creados_depto += 1

    municipios_unicos = df.drop_duplicates(subset=["Código Municipio"])
    municipios_por_nombre: dict[str, Municipio] = {}
    creados_mun = 0
    for _, fila in municipios_unicos.iterrows():
        cod_mun = str(int(fila["Código Municipio"])).zfill(5)
        cod_dep = str(int(fila["Código Departamento"])).zfill(2)
        depto = departamentos_por_codigo[cod_dep]
        nombre_mun = str(fila["Nombre Municipio"]).strip()
        antes = session.exec(select(Municipio).where(Municipio.codigo_dane == cod_mun)).first()
        municipio = _obtener_o_crear(
            session, Municipio, codigo_dane=cod_mun,
            defaults={"nombre": nombre_mun, "departamento_id": depto.id},
        )
        if antes is None:
            creados_mun += 1
        municipios_por_nombre[_normalizar(nombre_mun)] = municipio

    session.flush()
    return {
        "departamentos_en_archivo": len(deptos_unicos),
        "departamentos_creados_esta_corrida": creados_depto,
        "municipios_en_archivo": len(municipios_unicos),
        "municipios_creados_esta_corrida": creados_mun,
        "municipios_por_nombre": municipios_por_nombre,
    }


# --- Terceros ---


def cargar_terceros(
    session: Session, ruta: Path, municipios_por_nombre: dict[str, Municipio]
) -> dict[str, Any]:
    df = pd.read_excel(ruta, sheet_name="Terceros")
    df.columns = [str(c).strip() for c in df.columns]

    depto_fallback = _obtener_o_crear(
        session, Departamento, codigo_dane=DEPARTAMENTO_FALLBACK_CODIGO,
        defaults={"nombre": "Sin especificar"},
    )
    session.flush()
    municipio_fallback = _obtener_o_crear(
        session, Municipio, codigo_dane=MUNICIPIO_FALLBACK_CODIGO,
        defaults={"nombre": "Sin especificar", "departamento_id": depto_fallback.id},
    )
    session.flush()

    creados = 0
    reutilizados = 0
    duplicados_en_archivo = 0
    con_fallback: list[tuple[str, int]] = []
    vistos: set[str] = set()

    for _, fila in df.iterrows():
        identificacion = _texto_o_defecto(fila.get("CC o NIT"), "")
        if not identificacion:
            continue
        if identificacion in vistos:
            duplicados_en_archivo += 1
            continue
        vistos.add(identificacion)

        existente = session.exec(
            select(Tercero).where(Tercero.identificacion == identificacion)
        ).first()
        if existente is not None:
            reutilizados += 1
            continue

        nombre = _texto_o_defecto(fila.get("RAZON SOCIAL o NOMBRES Y APELLIDOS"), identificacion)
        direccion = _texto_o_defecto(fila.get("DIRECCIÓN"), "")
        email = _texto_o_defecto(fila.get("E-mail"), "")
        telefono = _texto_o_defecto(fila.get("Telefono"), "")
        regimen = _texto_o_defecto(fila.get("Regimen"), "No especificado")

        ciudad_raw = fila.get("CIUDAD")
        municipio = None
        if ciudad_raw is not None and not (isinstance(ciudad_raw, float) and pd.isna(ciudad_raw)):
            municipio = municipios_por_nombre.get(_normalizar(ciudad_raw))

        usa_fallback = municipio is None
        if municipio is None:
            municipio = municipio_fallback

        tercero = Tercero(
            identificacion=identificacion,
            nombre=nombre,
            direccion=direccion,
            municipio_id=municipio.id,
            email=email,
            telefono=telefono,
            regimen=regimen,
        )
        session.add(tercero)
        session.flush()
        creados += 1
        if usa_fallback:
            con_fallback.append((identificacion, tercero.id))

    if con_fallback:
        RUTA_REPORTE_SIN_MUNICIPIO.parent.mkdir(parents=True, exist_ok=True)
        with open(RUTA_REPORTE_SIN_MUNICIPIO, "w", newline="", encoding="utf-8") as f:
            escritor = csv.writer(f)
            escritor.writerow(["tercero_id", "identificacion"])
            for identificacion, tercero_id in con_fallback:
                escritor.writerow([tercero_id, identificacion])

    return {
        "creados": creados,
        "reutilizados": reutilizados,
        "duplicados_en_archivo": duplicados_en_archivo,
        "con_fallback_municipio": len(con_fallback),
        "reporte_sin_municipio": str(RUTA_REPORTE_SIN_MUNICIPIO) if con_fallback else None,
    }


# --- Empresa ---


def cargar_empresa(session: Session, ruta: Path) -> EmpresaGrupo:
    df = pd.read_excel(ruta, sheet_name="Empresa", header=None)
    campos = dict(zip(df[0].astype(str).str.strip(), df[1], strict=False))
    nombre = _texto_o_defecto(campos.get("Nombre Empresa"), "")
    if not nombre:
        raise RuntimeError("No se encontró 'Nombre Empresa' en la hoja Empresa.")
    empresa = _obtener_o_crear(session, EmpresaGrupo, nombre=nombre)
    session.flush()
    return empresa


# --- Configuracion: activos + catálogos ---


def cargar_configuracion(session: Session, ruta: Path, empresa: EmpresaGrupo) -> dict[str, Any]:
    df = pd.read_excel(ruta, sheet_name="Configuracion", header=0)
    df.columns = [str(c).strip() for c in df.columns]

    conteos: dict[str, int] = {}

    def _cargar_activos(columna: str, tipo_activo: str) -> int:
        creados = 0
        for placa in _valores_unicos_columna(df, columna):
            existente = session.exec(select(Activo).where(Activo.placa == placa)).first()
            if existente is None:
                session.add(
                    Activo(
                        placa=placa,
                        tipo_activo=tipo_activo,
                        clase="Sin especificar",
                        empresa_id=empresa.id,
                    )
                )
                creados += 1
        return creados

    conteos["activos_vehiculos"] = _cargar_activos("VEHICULOS", "Vehículo")
    conteos["activos_camabajas"] = _cargar_activos("CAMABAJAS", "Cama baja")
    session.flush()

    def _cargar_catalogo_nombre(
        columna: str, model, *, alias_normalizado: dict[str, str] | None = None
    ) -> int:
        """alias_normalizado mapea una clave normalizada (mayúsculas, sin
        acentos, sin espacios) del valor de origen hacia el nombre EXACTO ya
        existente en el catálogo, para no crear un duplicado cuando el
        archivo real usa una grafía distinta del mismo concepto (ej.
        'CAMABAJA' del Excel vs 'Cama baja' ya seedeado)."""
        alias_normalizado = alias_normalizado or {}
        creados = 0
        for nombre in _valores_unicos_columna(df, columna):
            clave = _normalizar(nombre).replace(" ", "")
            nombre_real = alias_normalizado.get(clave, nombre)
            existente = session.exec(select(model).where(model.nombre == nombre_real)).first()
            if existente is None:
                session.add(model(nombre=nombre_real))
                creados += 1
        return creados

    conteos["tipos_servicio"] = _cargar_catalogo_nombre(
        "DETALLE1", TipoServicio, alias_normalizado={"CAMABAJA": "Cama baja"}
    )
    conteos["productos"] = _cargar_catalogo_nombre(
        "DETALLE2", Producto, alias_normalizado={"GRAVILLA": "Gravilla", "RECEBO": "Recebo"}
    )
    conteos["formas_pago"] = _cargar_catalogo_nombre(
        "F PAGO", FormaPago, alias_normalizado={"CONTADO": "Contado", "CREDITO": "Crédito"}
    )
    conteos["unidades_medida"] = _cargar_catalogo_nombre(
        "U_medida",
        UnidadMedida,
        alias_normalizado={"TONELADAS": "Tonelada", "METROSCUBICOS": "Metro cúbico"},
    )
    session.flush()

    def _cargar_catalogo_codigo(columna: str, model, *, prefijo: bool = False) -> int:
        creados = 0
        for codigo in _valores_unicos_columna(df, columna):
            existente = session.exec(select(model).where(model.codigo == codigo)).first()
            if existente is None:
                if prefijo:
                    session.add(model(codigo=codigo, consecutivo_actual=0, es_manual=False))
                else:
                    session.add(model(codigo=codigo))
                creados += 1
        return creados

    conteos["prefijos"] = _cargar_catalogo_codigo("PrefijoRemisiones", Prefijo, prefijo=True)
    conteos["prefijos_factura"] = _cargar_catalogo_codigo("PrefijoFacturas", PrefijoFactura)
    session.flush()

    conteos["omitido_obracliente_proyectos"] = len(_valores_unicos_columna(df, "OBRACLIENTE"))
    conteos["omitido_obradetalle_tramos"] = len(_valores_unicos_columna(df, "OBRADETALLE"))
    return conteos


# --- preview (solo lectura, no toca la BD) ---


def preview(ruta: Path) -> None:
    print("=== PREVIEW — no se escribe nada en la base de datos ===\n")

    dane = _leer_dane(ruta)
    deptos = dane[["Código Departamento", "Nombre Departamento"]].drop_duplicates()
    municipios = dane.drop_duplicates(subset=["Código Municipio"])
    print(f"--- DANE ({len(dane)} filas en la hoja) ---")
    print(f"Departamentos únicos: {len(deptos)} -> {deptos['Nombre Departamento'].tolist()}")
    print(f"Municipios únicos (por Código Municipio): {len(municipios)}")
    print("Muestra mapeada a departamentos.codigo_dane/nombre y municipios.codigo_dane/nombre:")
    for _, fila in municipios.head(3).iterrows():
        print(
            f"  depto[codigo_dane={int(fila['Código Departamento']):02d}, "
            f"nombre={fila['Nombre Departamento']}]  "
            f"municipio[codigo_dane={int(fila['Código Municipio']):05d}, "
            f"nombre={fila['Nombre Municipio']}]"
        )

    terc = pd.read_excel(ruta, sheet_name="Terceros")
    terc.columns = [str(c).strip() for c in terc.columns]
    print(f"\n--- Terceros ({len(terc)} filas en la hoja) ---")
    print(f"CC o NIT duplicados en el archivo: {terc['CC o NIT'].duplicated().sum()}")
    print("Muestra mapeada a terceros.identificacion/nombre/direccion/email/telefono/regimen/municipio(ciudad):")
    for _, fila in terc.head(3).iterrows():
        print(
            f"  identificacion={_texto_o_defecto(fila.get('CC o NIT'), '')!r} "
            f"nombre={_texto_o_defecto(fila.get('RAZON SOCIAL o NOMBRES Y APELLIDOS'), '')!r} "
            f"direccion={_texto_o_defecto(fila.get('DIRECCIÓN'), '')!r} "
            f"email={_texto_o_defecto(fila.get('E-mail'), '')!r} "
            f"telefono={_texto_o_defecto(fila.get('Telefono'), '')!r} "
            f"regimen={_texto_o_defecto(fila.get('Regimen'), 'No especificado')!r} "
            f"ciudad={fila.get('CIUDAD')!r}"
        )

    empresa_df = pd.read_excel(ruta, sheet_name="Empresa", header=None)
    campos = dict(zip(empresa_df[0].astype(str).str.strip(), empresa_df[1], strict=False))
    print("\n--- Empresa ---")
    print(f"empresas_grupo.nombre = {_texto_o_defecto(campos.get('Nombre Empresa'), '')!r}")

    cfg = pd.read_excel(ruta, sheet_name="Configuracion", header=0)
    cfg.columns = [str(c).strip() for c in cfg.columns]
    print(f"\n--- Configuracion ({len(cfg)} filas en la hoja) ---")
    mapeos = [
        ("VEHICULOS", "activos (tipo_activo='Vehículo')"),
        ("CAMABAJAS", "activos (tipo_activo='Cama baja')"),
        ("DETALLE1", "tipos_servicio"),
        ("DETALLE2", "productos"),
        ("F PAGO", "formas_pago"),
        ("U_medida", "unidades_medida"),
        ("PrefijoRemisiones", "prefijos"),
        ("PrefijoFacturas", "prefijos_factura"),
    ]
    for columna, destino in mapeos:
        valores = _valores_unicos_columna(cfg, columna)
        print(f"  {columna} ({len(valores)} valores únicos) -> {destino}. Ejemplo: {valores[:3]}")
    print(
        f"  OBRACLIENTE ({len(_valores_unicos_columna(cfg, 'OBRACLIENTE'))} valores) y "
        f"OBRADETALLE+KM2 ({len(_valores_unicos_columna(cfg, 'OBRADETALLE'))} valores) "
        "-> OMITIDOS esta pasada (no traen cliente_id/proyecto_id)."
    )
    print(
        "  DEPARTAMENTOS/CIUDADES (listas de referencia del propio archivo) -> IGNORADOS, "
        "se usa la hoja DANE como fuente canónica."
    )

    print(
        "\nDETALLE1: 'CAMABAJA' se resuelve por alias hacia el 'Cama baja' ya existente "
        "(no crea un tipo_servicio nuevo)."
    )
    print(
        "U_medida: 'TONELADAS' -> 'Tonelada' y 'METROS CUBICOS' -> 'Metro cúbico' "
        "(se resuelven por alias hacia el singular ya existente)."
    )
    print(
        "DETALLE2: 'GRAVILLA' -> 'Gravilla' y 'RECEBO' -> 'Recebo' "
        "(se resuelven por alias hacia el registro ya existente)."
    )
    print(
        "F PAGO: 'CONTADO' -> 'Contado' y 'CREDITO' -> 'Crédito' "
        "(se resuelven por alias hacia el registro ya existente)."
    )

    _mostrar_hallazgos_coincidencia(cfg)


def _mostrar_hallazgos_coincidencia(cfg: pd.DataFrame) -> None:
    """Compara (mayúsculas, sin acentos, sin espacios) los valores de cada
    columna de Configuracion contra lo que YA existe en la base (de los
    seeds de las Partes 3-6), para detectar posibles duplicados por
    grafía distinta. Solo informa — no decide ni corrige nada aquí."""
    print("\n--- Hallazgos de posible coincidencia con catálogos ya existentes ---")
    catalogos_nombre = [
        ("DETALLE1 -> tipos_servicio", "DETALLE1", TipoServicio, {"CAMABAJA": "Cama baja"}),
        (
            "DETALLE2 -> productos",
            "DETALLE2",
            Producto,
            {"GRAVILLA": "Gravilla", "RECEBO": "Recebo"},
        ),
        (
            "F PAGO -> formas_pago",
            "F PAGO",
            FormaPago,
            {"CONTADO": "Contado", "CREDITO": "Crédito"},
        ),
        (
            "U_medida -> unidades_medida",
            "U_medida",
            UnidadMedida,
            {"TONELADAS": "Tonelada", "METROSCUBICOS": "Metro cúbico"},
        ),
    ]
    with Session(engine) as session:
        for etiqueta, columna, model, alias_ya_resuelto in catalogos_nombre:
            existentes = {
                _normalizar(o.nombre).replace(" ", ""): o.nombre
                for o in session.exec(select(model)).all()
            }
            coincidencias = []
            for valor in _valores_unicos_columna(cfg, columna):
                clave = _normalizar(valor).replace(" ", "")
                if clave in alias_ya_resuelto:
                    continue  # ya resuelto explícitamente, no es un hallazgo nuevo
                if clave in existentes and existentes[clave] != valor:
                    coincidencias.append((valor, existentes[clave]))
            if coincidencias:
                print(f"  [{etiqueta}] valor del Excel == ya existe en BD (distinta grafía):")
                for valor_excel, valor_bd in coincidencias:
                    print(f"    '{valor_excel}'  <->  '{valor_bd}'")
            else:
                print(f"  [{etiqueta}] sin coincidencias adicionales.")

        # Prefijo y PrefijoFactura: coincidencia exacta por codigo (case-sensitive),
        # que get_or_create YA maneja de forma segura (reutiliza, no duplica).
        for etiqueta, columna, model in [
            ("PrefijoRemisiones -> prefijos", "PrefijoRemisiones", Prefijo),
            ("PrefijoFacturas -> prefijos_factura", "PrefijoFacturas", PrefijoFactura),
        ]:
            existentes_codigo = {o.codigo for o in session.exec(select(model)).all()}
            iguales = [
                v for v in _valores_unicos_columna(cfg, columna) if v in existentes_codigo
            ]
            if iguales:
                print(
                    f"  [{etiqueta}] códigos EXACTOS que ya existen (se reutilizan, no se "
                    f"duplican): {iguales}"
                )


def importar(ruta: Path) -> dict[str, Any]:
    with Session(engine) as session:
        resultado_dane = cargar_dane(session, ruta)
        session.commit()

        resultado_terceros = cargar_terceros(session, ruta, resultado_dane["municipios_por_nombre"])
        session.commit()

        empresa = cargar_empresa(session, ruta)
        nombre_empresa = empresa.nombre  # leer antes de que el commit expire el objeto
        session.commit()

        resultado_config = cargar_configuracion(session, ruta, empresa)
        session.commit()

    return {
        "dane": {k: v for k, v in resultado_dane.items() if k != "municipios_por_nombre"},
        "terceros": resultado_terceros,
        "empresa": nombre_empresa,
        "configuracion": resultado_config,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--preview", action="store_true", help="Solo muestra el preview, no toca la BD.")
    grupo.add_argument("--aplicar", action="store_true", help="Inserta los datos reales en la BD.")
    args = parser.parse_args()

    if args.preview:
        preview(RUTA_EXCEL)
    else:
        resultado = importar(RUTA_EXCEL)
        print("Importación completada:")
        for seccion, datos in resultado.items():
            print(f"  {seccion}: {datos}")
