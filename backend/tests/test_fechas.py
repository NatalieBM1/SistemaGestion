"""Parte 6.2: criterio único de fechas = UTC sin zona (core/fechas.py).

Las pruebas sobre Postgres corren dentro de una transacción que se revierte
al final: no queda nada escrito en el clon (TEST_DATABASE_URL)."""

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlmodel import Session, select

from app.core.fechas import ahora_utc
from app.core.security import create_access_token, decode_token
from app.models.auditoria import Auditoria
from app.models.facturacion import RemisionFacturacion
from app.models.remision import Remision
from app.models.usuario import Usuario
from app.services.facturacion_service import anular_facturacion

APP = Path(__file__).resolve().parents[1] / "app"


def _cerca_de_ahora(valor: datetime) -> bool:
    return valor.tzinfo is None and abs(ahora_utc() - valor) < timedelta(seconds=30)


def test_ahora_utc_es_utc_sin_zona():
    valor = ahora_utc()
    assert valor.tzinfo is None
    utc = datetime.now(timezone.utc).replace(tzinfo=None)
    assert abs(utc - valor) < timedelta(seconds=2)


def test_no_queda_utcnow_en_el_codigo():
    usos = [
        f"{p.relative_to(APP)}:{n}"
        for p in APP.rglob("*.py")
        if p.name != "fechas.py"
        for n, linea in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
        if re.search(r"\butcnow\(|datetime\.utcnow\b", linea)
    ]
    assert usos == []


# ── Creación / actualización (modelos) ───────────────────────────────────────


def test_creado_y_actualizado_en_al_crear_y_al_modificar(engine_prueba):
    with Session(engine_prueba) as s:
        u = s.exec(select(Usuario)).one()
        assert _cerca_de_ahora(u.creado_en) and _cerca_de_ahora(u.actualizado_en)
        antes = u.actualizado_en
        u.nombre = "Otro nombre"
        s.add(u)
        s.commit()
        s.refresh(u)
        assert u.actualizado_en.tzinfo is None
        assert u.actualizado_en >= antes


# ── Tokens y códigos ─────────────────────────────────────────────────────────


def test_token_vencido_se_rechaza(client_api, engine_prueba):
    with Session(engine_prueba) as s:
        uid = s.exec(select(Usuario)).one().id
    vencido = create_access_token({"sub": str(uid)}, expires_delta=timedelta(seconds=-1))
    resp = client_api.get("/api/auth/me", headers={"Authorization": f"Bearer {vencido}"})
    assert resp.status_code == 401
    assert "expirado" in resp.json()["detail"]


def test_exp_del_token_es_la_hora_utc_correcta():
    token = create_access_token({"sub": "1"}, expires_delta=timedelta(minutes=60))
    exp = datetime.fromtimestamp(decode_token(token)["exp"], tz=timezone.utc).replace(tzinfo=None)
    assert abs(exp - (ahora_utc() + timedelta(minutes=60))) < timedelta(seconds=5)


def test_codigo_de_recuperacion_vence_en_utc(client_api, correos, engine_prueba):
    client_api.post("/api/auth/forgot-password", json={"email": "prueba@example.com"})
    with Session(engine_prueba) as s:
        expira = s.exec(select(Usuario)).one().reset_token_expires
    assert expira.tzinfo is None
    assert timedelta(minutes=14) < expira - ahora_utc() <= timedelta(minutes=15)


# ── Postgres real (clon), con rollback ───────────────────────────────────────


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


def test_fechas_guardadas_hoy_son_naive_y_comparables(session_con_rollback):
    s = session_con_rollback
    remision = s.exec(select(Remision).order_by(Remision.creado_en.desc())).first()
    assert remision.creado_en.tzinfo is None
    # Comparar lo guardado con ahora_utc() no lanza TypeError (naive vs naive).
    assert remision.creado_en < ahora_utc()


def test_actualizado_en_de_remision_en_postgres(session_con_rollback):
    s = session_con_rollback
    remision = s.exec(select(Remision).order_by(Remision.id)).first()
    remision.observaciones = (remision.observaciones or "") + " [prueba]"
    s.add(remision)
    s.flush()
    s.refresh(remision)
    assert _cerca_de_ahora(remision.actualizado_en)


def test_anular_facturacion_guarda_anulada_en_utc(session_con_rollback):
    s = session_con_rollback
    registro = s.exec(
        select(RemisionFacturacion).where(RemisionFacturacion.anulada.is_(False))
    ).first()
    assert registro is not None
    auditorias_antes = s.exec(select(Auditoria.id)).all()

    anular_facturacion(s, registro, usuario_id=None)
    s.flush()
    s.expire_all()

    guardado = s.get(RemisionFacturacion, registro.id)
    assert guardado.anulada and _cerca_de_ahora(guardado.anulada_en)
    nuevas = s.exec(select(Auditoria).where(Auditoria.id.notin_(auditorias_antes))).all()
    assert nuevas and all(_cerca_de_ahora(a.creado_en) for a in nuevas)
