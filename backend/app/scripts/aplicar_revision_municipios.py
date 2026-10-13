"""Aplica en bloque el CSV `terceros_revision_manual.csv` una vez que alguien
llenó la columna `municipio_final` a mano.

Por defecto corre en modo vista previa (no escribe nada). Con --aplicar
hace un pg_dump de respaldo primero, y luego actualiza `terceros.municipio_id`
solo para las filas que tengan `municipio_final` no vacío y que coincida
exactamente (sin tildes, insensible a mayúsculas) con un `municipios.nombre`
existente. Las filas con un valor que no coincide con ningún municipio se
reportan como error y no se tocan (nunca se crea un municipio nuevo desde
aquí ni se adivina nada).

Uso:
    python -m app.scripts.aplicar_revision_municipios --db-url "postgresql://..."            (vista previa)
    python -m app.scripts.aplicar_revision_municipios --db-url "postgresql://..." --aplicar   (aplica, con respaldo previo)
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import unicodedata
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, create_engine, select

from app.models.tercero import Tercero
from app.models.ubicacion import Municipio

RUTA_CSV = Path(__file__).resolve().parents[1] / "data_import" / "terceros_revision_manual.csv"
RUTA_BACKUPS = Path(__file__).resolve().parents[1] / "data_import" / "backups"


def _normalizar(texto: str) -> str:
    texto = texto.strip().upper()
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def _respaldar(db_url: str) -> Path:
    RUTA_BACKUPS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = RUTA_BACKUPS / f"backup_{ts}_pre_revision_municipios.dump"
    # Usa pg_dump vía docker exec sobre el contenedor sistemagestion-db,
    # igual que el resto de respaldos de esta carga histórica.
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

    with open(RUTA_CSV, newline="", encoding="utf-8") as f:
        filas = [r for r in csv.DictReader(f) if r.get("municipio_final", "").strip()]

    if not filas:
        print("No hay ninguna fila con 'municipio_final' llenado. Nada que hacer.")
        return

    engine = create_engine(args.db_url)
    with Session(engine) as session:
        municipios_por_nombre = {
            _normalizar(m.nombre): m for m in session.exec(select(Municipio)).all()
        }

        a_aplicar: list[tuple[Tercero, Municipio]] = []
        errores: list[dict[str, str]] = []

        for fila in filas:
            tercero = session.get(Tercero, int(fila["id"]))
            if tercero is None:
                errores.append({"id": fila["id"], "motivo": "no existe ese tercero_id en esta base"})
                continue
            municipio = municipios_por_nombre.get(_normalizar(fila["municipio_final"]))
            if municipio is None:
                errores.append({
                    "id": fila["id"],
                    "motivo": f"'{fila['municipio_final']}' no coincide con ningún municipio del catálogo",
                })
                continue
            a_aplicar.append((tercero, municipio))

        print(f"Filas con municipio_final llenado: {len(filas)}")
        print(f"  se pueden aplicar: {len(a_aplicar)}")
        print(f"  con error (no se tocan): {len(errores)}")
        for e in errores:
            print(f"    - id={e['id']}: {e['motivo']}")

        if not args.aplicar:
            print("\nVista previa (no se escribió nada). Corre con --aplicar para ejecutar.")
            return

        if not a_aplicar:
            print("\nNada para aplicar.")
            return

        print("\nHaciendo respaldo antes de aplicar...")
        ruta_backup = _respaldar(args.db_url)
        print(f"Respaldo: {ruta_backup}")

        for tercero, municipio in a_aplicar:
            tercero.municipio_id = municipio.id
            session.add(tercero)
        session.commit()
        print(f"\nAplicado: {len(a_aplicar)} terceros actualizados.")


if __name__ == "__main__":
    main()
