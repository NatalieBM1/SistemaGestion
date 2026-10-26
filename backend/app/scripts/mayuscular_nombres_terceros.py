"""Convierte a MAYÚSCULAS el nombre de los terceros existentes que todavía
no lo están (conservando tildes). No toca nada por defecto — solo muestra
la vista previa (cuántos y cuáles cambiarían). Los terceros nuevos ya se
guardan en mayúsculas automáticamente desde el router; este script es
solo para normalizar los que ya existían antes de ese cambio.

Uso:
    python -m app.scripts.mayuscular_nombres_terceros --db-url "postgresql://..."             (vista previa)
    python -m app.scripts.mayuscular_nombres_terceros --db-url "postgresql://..." --aplicar    (aplica, con respaldo previo)
"""

from __future__ import annotations

import argparse
import subprocess
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, create_engine, select

from app.models.tercero import Tercero

RUTA_BACKUPS = Path(__file__).resolve().parents[1] / "data_import" / "backups"


def _respaldar(db_url: str) -> Path:
    RUTA_BACKUPS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = RUTA_BACKUPS / f"backup_{ts}_pre_mayuscular_terceros.dump"
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

    engine = create_engine(args.db_url)
    with Session(engine) as session:
        terceros = session.exec(select(Tercero)).all()
        a_cambiar = [t for t in terceros if t.nombre != t.nombre.upper()]

        print(f"Terceros totales: {len(terceros)}")
        print(f"Terceros cuyo nombre cambiaría a mayúsculas: {len(a_cambiar)}")
        for t in a_cambiar:
            print(f"  [{t.id}] {t.nombre!r} -> {t.nombre.upper()!r}")

        if not args.aplicar:
            print("\nVista previa (no se escribió nada). Corre con --aplicar para ejecutar.")
            return

        if not a_cambiar:
            print("\nNada para aplicar.")
            return

        print("\nHaciendo respaldo antes de aplicar...")
        ruta_backup = _respaldar(args.db_url)
        print(f"Respaldo: {ruta_backup}")

        for t in a_cambiar:
            t.nombre = t.nombre.upper()
            session.add(t)
        session.commit()
        print(f"\nAplicado: {len(a_cambiar)} terceros actualizados.")


if __name__ == "__main__":
    main()
