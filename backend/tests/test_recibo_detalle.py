"""Bloque 6: el detalle de la remisión trae lo que imprime el recibo:
"Vendedor" (quien la creó), su "CC No" (usuarios.identificacion, vacío si
no la tiene) y la placa de la cama baja junto al vehículo. Sobre el clon,
dentro de una transacción que se revierte."""

import pytest
from sqlmodel import Session, select

from app.models.activo import Activo
from app.models.remision import Remision
from app.models.usuario import Usuario
from app.services.remision_service import serializar_remision_detalle


@pytest.fixture
def s(pg_engine):
    conexion = pg_engine.connect()
    transaccion = conexion.begin()
    session = Session(bind=conexion, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaccion.rollback()
        conexion.close()


def test_vendedor_sin_identificacion_queda_en_blanco(s):
    r = s.exec(select(Remision).where(Remision.usuario_creador_id.is_not(None))).first()
    creador = s.get(Usuario, r.usuario_creador_id)
    creador.identificacion = None
    s.add(creador)
    s.flush()
    d = serializar_remision_detalle(s, r)
    assert d.usuario_creador_nombre == creador.nombre
    assert d.usuario_creador_identificacion is None


def test_vendedor_con_identificacion(s):
    r = s.exec(select(Remision).where(Remision.usuario_creador_id.is_not(None))).first()
    creador = s.get(Usuario, r.usuario_creador_id)
    creador.identificacion = "0087491991"
    s.add(creador)
    s.flush()
    assert serializar_remision_detalle(s, r).usuario_creador_identificacion == "0087491991"


def test_placa_de_cama_baja(s):
    con = s.exec(select(Remision).where(Remision.camabaja_id.is_not(None))).first()
    assert serializar_remision_detalle(s, con).camabaja_placa == s.get(Activo, con.camabaja_id).placa
    sin = s.exec(select(Remision).where(Remision.camabaja_id.is_(None))).first()
    assert serializar_remision_detalle(s, sin).camabaja_placa is None
