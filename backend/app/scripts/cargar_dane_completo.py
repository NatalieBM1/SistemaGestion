"""Carga el catálogo nacional completo de departamentos y municipios DANE
desde el Excel censal del cliente (hoja "Municipios" + hoja "Códigos DANE
Departamentos"), sin tocar los códigos que ya existen.

Idempotente por `codigo_dane` (texto, con ceros a la izquierda): si el
código ya existe, NO se duplica ni se le cambia el nombre (aunque difiera
del Excel) — esos casos solo se reportan, nunca se sobreescriben
automáticamente. Solo se insertan los códigos que todavía no existen.

Uso:
    python -m app.scripts.cargar_dane_completo --db-url "postgresql://..."               (vista previa, no escribe nada)
    python -m app.scripts.cargar_dane_completo --db-url "postgresql://..." --aplicar      (hace un pg_dump de respaldo y aplica)
"""

from __future__ import annotations

import argparse
import subprocess
import unicodedata
from datetime import datetime
from pathlib import Path

import openpyxl
from sqlmodel import Session, create_engine, select

from app.models.ubicacion import Departamento, Municipio

RUTA_EXCEL = (
    Path(__file__).resolve().parents[1]
    / "data_import"
    / "formatos"
    / "Listado-censal-consejos-organizaciones-base-formas-y-expr.-organizativas.-Anexo-3.-Vr-02-25-02-2022.xlsx"
)
RUTA_BACKUPS = Path(__file__).resolve().parents[1] / "data_import" / "backups"


def _normalizar(texto) -> str:
    texto = str(texto).strip().upper()
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def _leer_departamentos(wb) -> dict[str, str]:
    """-> {codigo_dane (2 dígitos): nombre}"""
    hoja = next(n for n in wb.sheetnames if "Departamentos" in n)
    ws = wb[hoja]
    deptos: dict[str, str] = {}
    for row in range(2, ws.max_row + 1):
        codigo = ws.cell(row=row, column=1).value
        nombre = ws.cell(row=row, column=2).value
        if codigo is None or nombre is None:
            continue
        deptos[str(codigo).strip().zfill(2)] = str(nombre).strip()
    return deptos


def _leer_municipios(wb) -> list[tuple[str, str, str]]:
    """-> [(codigo_dane 5 dígitos, nombre_municipio, nombre_departamento), ...]"""
    ws = wb["Municipios"]
    filas: list[tuple[str, str, str]] = []
    for row in range(2, ws.max_row + 1):
        codigo = ws.cell(row=row, column=1).value
        municipio = ws.cell(row=row, column=2).value
        departamento = ws.cell(row=row, column=3).value
        if codigo is None or municipio is None:
            continue
        filas.append((str(codigo).strip().zfill(5), str(municipio).strip(), str(departamento).strip()))
    return filas


def _respaldar(db_url: str) -> Path:
    RUTA_BACKUPS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = RUTA_BACKUPS / f"backup_{ts}_pre_dane_completo.dump"
    tmp_en_contenedor = f"/tmp/backup_{ts}.dump"
    subprocess.run(
        ["docker", "exec", "sistemagestion-db", "pg_dump", "-U", "remisiones", "-d", "remisiones",
         "-Fc", "-f", tmp_en_contenedor],
        check=True,
    )
    subprocess.run(["docker", "cp", f"sistemagestion-db:{tmp_en_contenedor}", str(destino)], check=True)
    subprocess.run(["docker", "exec", "sistemagestion-db", "rm", tmp_en_contenedor], check=True)
    return destino


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-url", required=True)
    parser.add_argument("--aplicar", action="store_true", help="Si no se pasa, solo muestra vista previa.")
    args = parser.parse_args()

    wb = openpyxl.load_workbook(RUTA_EXCEL, data_only=True)
    deptos_excel = _leer_departamentos(wb)
    municipios_excel = _leer_municipios(wb)
    print(f"Excel: {len(deptos_excel)} departamentos, {len(municipios_excel)} municipios.")

    engine = create_engine(args.db_url)
    with Session(engine) as session:
        deptos_db = {d.codigo_dane: d for d in session.exec(select(Departamento)).all()}
        municipios_db = {m.codigo_dane: m for m in session.exec(select(Municipio)).all()}

        deptos_a_crear: list[tuple[str, str]] = []
        deptos_difieren: list[tuple[str, str, str]] = []
        for codigo, nombre in deptos_excel.items():
            existente = deptos_db.get(codigo)
            if existente is None:
                deptos_a_crear.append((codigo, nombre))
            elif _normalizar(existente.nombre) != _normalizar(nombre):
                deptos_difieren.append((codigo, existente.nombre, nombre))

        municipios_a_crear: list[tuple[str, str, str]] = []
        municipios_difieren: list[tuple[str, str, str]] = []
        municipios_sin_depto: list[tuple[str, str, str]] = []

        # Departamento por nombre normalizado, incluyendo los que se van a
        # crear en esta misma corrida (para resolver dependencias dentro
        # del propio Excel).
        depto_id_por_nombre: dict[str, int | str] = {
            _normalizar(d.nombre): d.id for d in deptos_db.values()
        }
        for codigo, nombre in deptos_a_crear:
            depto_id_por_nombre[_normalizar(nombre)] = f"NUEVO:{codigo}"

        for codigo, nombre_municipio, nombre_departamento in municipios_excel:
            existente = municipios_db.get(codigo)
            if existente is not None:
                if _normalizar(existente.nombre) != _normalizar(nombre_municipio):
                    municipios_difieren.append((codigo, existente.nombre, nombre_municipio))
                continue
            if _normalizar(nombre_departamento) not in depto_id_por_nombre:
                municipios_sin_depto.append((codigo, nombre_municipio, nombre_departamento))
                continue
            municipios_a_crear.append((codigo, nombre_municipio, nombre_departamento))

        print()
        print(f"Departamentos a crear: {len(deptos_a_crear)}")
        for codigo, nombre in deptos_a_crear:
            print(f"  + {codigo} {nombre}")
        print(f"Departamentos que ya existen con nombre distinto (NO se tocan): {len(deptos_difieren)}")
        for codigo, nombre_db, nombre_excel in deptos_difieren:
            print(f"  ! {codigo}: en la base '{nombre_db}' vs Excel '{nombre_excel}'")

        print()
        print(f"Municipios a crear: {len(municipios_a_crear)}")
        print(f"Municipios que ya existen con nombre distinto (NO se tocan): {len(municipios_difieren)}")
        for codigo, nombre_db, nombre_excel in municipios_difieren:
            print(f"  ! {codigo}: en la base '{nombre_db}' vs Excel '{nombre_excel}'")
        if municipios_sin_depto:
            print(f"Municipios sin departamento resoluble (no se crean): {len(municipios_sin_depto)}")
            for fila in municipios_sin_depto:
                print(f"  ? {fila}")

        if not args.aplicar:
            print("\nVista previa (no se escribió nada). Corre con --aplicar para ejecutar.")
            return

        print("\nHaciendo respaldo antes de aplicar...")
        ruta_backup = _respaldar(args.db_url)
        print(f"Respaldo: {ruta_backup}")

        nuevo_id_departamento: dict[str, int] = {}
        for codigo, nombre in deptos_a_crear:
            depto = Departamento(codigo_dane=codigo, nombre=nombre)
            session.add(depto)
            session.flush()
            nuevo_id_departamento[_normalizar(nombre)] = depto.id

        for codigo, nombre_municipio, nombre_departamento in municipios_a_crear:
            clave = _normalizar(nombre_departamento)
            depto_existente = next(
                (d for d in deptos_db.values() if _normalizar(d.nombre) == clave), None
            )
            departamento_id = (
                depto_existente.id if depto_existente else nuevo_id_departamento[clave]
            )
            session.add(
                Municipio(codigo_dane=codigo, nombre=nombre_municipio, departamento_id=departamento_id)
            )

        session.commit()
        print(f"\nAplicado: {len(deptos_a_crear)} departamentos y {len(municipios_a_crear)} municipios nuevos.")


if __name__ == "__main__":
    main()
