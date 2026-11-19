# ruff: noqa: DTZ001 — los nombres de respaldo usan la hora local a propósito
"""Rotación y cifrado de scripts/respaldo.py (sin base de datos)."""

import datetime as dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import _respaldos_comun as R


def _archivos(tmp_path, desde: dt.datetime, dias: int) -> list[Path]:
    salida = []
    for i in range(dias):
        f = tmp_path / f"respaldo_remisiones_{(desde + dt.timedelta(days=i)):%Y%m%d}_020000.dump.enc"
        f.write_bytes(b"x")
        salida.append(f)
    return salida


def test_rotacion_14_diarios_8_semanales_mensuales_y_anuales(tmp_path):
    hoy = dt.datetime(2026, 11, 16, 3, 0)
    archivos = _archivos(tmp_path, dt.datetime(2014, 1, 1, 2, 0), (hoy - dt.datetime(2014, 1, 1)).days + 1)
    conservar = R.a_conservar(archivos, diarios=14, semanales=8, anios_mensuales=10, anios_anuales=10, hoy=hoy)
    etiquetas = R.clasificar(archivos)
    ordenados = sorted(archivos, key=R.fecha_de, reverse=True)
    # Los 14 más recientes siempre se conservan.
    assert set(ordenados[:14]) <= conservar
    # 8 semanales (el último de cada semana).
    assert len([f for f in ordenados if "semanal" in etiquetas[f]][:8]) == 8
    # Mensuales y anuales de los últimos 10 años: todos conservados.
    limite = hoy.replace(year=hoy.year - 10)
    mensuales = [f for f in archivos if "mensual" in etiquetas[f] and R.fecha_de(f) >= limite]
    assert len(mensuales) >= 120 and set(mensuales) <= conservar
    # Nada de más de 10 años, salvo lo que no es mensual ni anual (ya borrado).
    assert all(R.fecha_de(f) >= limite for f in conservar)
    # Lo demás se borra.
    assert len(conservar) < len(archivos)


def test_cifrado_ida_y_vuelta_y_clave_incorrecta():
    datos = b"PGDMP" + bytes(range(256)) * 50
    cifrado = R.cifrar(datos, "una frase de prueba larga")
    assert cifrado.startswith(R.MAGIA) and datos not in cifrado
    assert R.descifrar(cifrado, "una frase de prueba larga") == datos
    with pytest.raises(SystemExit):
        R.descifrar(cifrado, "otra frase distinta")


def test_destino_dentro_del_repo_se_rechaza():
    with pytest.raises(SystemExit):
        R.destino_fuera_del_repo(R.RAIZ_REPO / "respaldos")


def test_subir_sin_credenciales_avisa(monkeypatch):
    for v in ("S3_ENDPOINT", "S3_BUCKET", "S3_REGION", "S3_ACCESS_KEY_ID", "S3_SECRET_ACCESS_KEY"):
        monkeypatch.delenv(v, raising=False)
    with pytest.raises(SystemExit):
        R.subir_s3(b"x", "diario/x")
