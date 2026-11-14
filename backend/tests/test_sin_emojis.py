"""Bloque 1: la interfaz, los mensajes del backend, los correos, lo impreso
y los datos semilla no llevan emojis. Los íconos (lucide-react / SVG) no son
texto y no cuentan. Los comentarios de código sí se escanean: si alguien
pega un emoji en un comentario, que lo quite también."""

import re
from pathlib import Path

import openpyxl

RAIZ = Path(__file__).resolve().parents[2]
# Rangos por número de código (el archivo queda en ASCII puro, sin los símbolos).
RANGOS = [(0x1F000, 0x1FAFF), (0x2600, 0x27BF), (0x2B00, 0x2BFF), (0x25A0, 0x25FF)]
SUELTOS = [0xFE0F, 0x200D]
EMOJI = re.compile(
    "[" + "".join(f"{chr(a)}-{chr(b)}" for a, b in RANGOS) + "".join(map(chr, SUELTOS)) + "]"
)
EXTENSIONES = {".ts", ".tsx", ".css", ".html", ".py", ".json", ".svg"}


def _archivos():
    for carpeta in (RAIZ / "frontend" / "src", RAIZ / "backend" / "app", RAIZ / "backend" / "alembic"):
        for f in carpeta.rglob("*"):
            if f.suffix in EXTENSIONES and "__pycache__" not in f.parts:
                yield f
    yield RAIZ / "frontend" / "index.html"


def test_codigo_sin_emojis():
    hallados = [
        f"{f.relative_to(RAIZ)}:{n}: {linea.strip()[:80]}"
        for f in _archivos()
        for n, linea in enumerate(f.read_text(encoding="utf-8").splitlines(), 1)
        if EMOJI.search(linea)
    ]
    assert hallados == []


def test_excel_semilla_sin_emojis():
    wb = openpyxl.load_workbook(RAIZ / "backend" / "app" / "seed_files" / "ejemplo_facturar_masivo.xlsx")
    celdas = [
        c.value for ws in wb for fila in ws.iter_rows() for c in fila
        if isinstance(c.value, str) and EMOJI.search(c.value)
    ]
    assert celdas == []
