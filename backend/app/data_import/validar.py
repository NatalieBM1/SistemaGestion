"""Cifras de control: lo que dice el Excel contra lo que quedó en la base
(Bloque 3). Solo conteos y sumas; ningún dato personal."""

from __future__ import annotations

from collections import Counter, defaultdict
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import text
from sqlmodel import Session

from app.core import numero_remision as numero_remision_svc
from app.data_import.lector import Libro

CERO = Decimal(0)
CENTAVO = Decimal("0.01")


def centavos(valor) -> Decimal:
    """Como lo guarda la base (numeric(14,2), redondeo al centavo)."""
    return Decimal(valor or 0).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def _vacio_sumas() -> dict[str, Decimal]:
    return {"material": CERO, "flete": CERO, "camabaja": CERO, "facturado": CERO}


def estadisticas_excel(libro: Libro) -> dict:
    L = libro.lineas
    por_anio: dict[int, dict[str, Decimal]] = defaultdict(_vacio_sumas)
    facturado_por_anio_factura: dict[int, Decimal] = defaultdict(lambda: CERO)
    for ln in L:
        a = por_anio[ln.fecha.year]
        a["material"] += centavos(ln.valor_material)
        a["flete"] += centavos(ln.valor_flete)
        a["camabaja"] += centavos(ln.valor_camabaja)
        a["facturado"] += centavos(ln.vr_facturado)
        if ln.factura and ln.fecha_factura:
            facturado_por_anio_factura[ln.fecha_factura.year] += centavos(ln.vr_parcial if ln.vr_parcial is not None else ln.vr_facturado)
    prefijos = defaultdict(lambda: [0, set()])
    for ln in L:
        prefijos[ln.prefijo][0] += 1
        prefijos[ln.prefijo][1].add(ln.consecutivo)
    return {
        "registros": len(L),
        "remisiones": len(libro.remisiones),
        "facturas": len({ln.factura for ln in L if ln.factura}),
        "clientes": len({ln.cliente_id for ln in L if ln.cliente_id}),
        "conductores": len({ln.conductor_id for ln in L if ln.conductor_id}),
        "placas": len({ln.vehiculo for ln in L if ln.vehiculo}),
        "productos": len({ln.producto for ln in L if ln.producto}),
        "lineas_por_estado": Counter(ln.estado or "(sin estado)" for ln in L),
        "prefijos": {p: (v[0], len(v[1])) for p, v in sorted(prefijos.items())},
        "por_anio": dict(sorted(por_anio.items())),
        "facturado_por_anio_factura": dict(sorted(facturado_por_anio_factura.items())),
    }


def estadisticas_bd(session: Session, libro: Libro) -> dict:
    """Mismas cifras, solo sobre las remisiones de la base cuyo número está
    en el Excel (así sirve también en una base con otras remisiones)."""
    claves_excel = set(libro.remisiones)
    filas = session.exec(text("SELECT id, numero_remision FROM remisiones")).all()
    ids = [i for i, numero in filas if numero_remision_svc.clave(numero) in claves_excel]
    if not ids:
        return {"remisiones": 0}
    session.exec(text("CREATE TEMP TABLE IF NOT EXISTS _ids_carga (id int primary key) ON COMMIT DROP"))
    session.exec(text("DELETE FROM _ids_carga"))
    for i in range(0, len(ids), 5000):
        valores = ",".join(f"({x})" for x in ids[i : i + 5000])
        session.exec(text(f"INSERT INTO _ids_carga (id) VALUES {valores}"))

    def uno(sql: str):
        return session.exec(text(sql)).one()

    lineas = uno("SELECT count(*) FROM remision_productos p JOIN _ids_carga i ON i.id = p.remision_id")[0]
    resultado = {
        "remisiones": len(ids),
        "registros": lineas,
        "facturas": uno(
            "SELECT count(DISTINCT rf.factura_id) FROM remision_facturacion rf JOIN _ids_carga i ON i.id = rf.remision_id WHERE NOT rf.anulada"
        )[0],
        "clientes": uno("SELECT count(DISTINCT cliente_id) FROM remisiones r JOIN _ids_carga i ON i.id = r.id")[0],
        "conductores": uno("SELECT count(DISTINCT conductor_id) FROM remisiones r JOIN _ids_carga i ON i.id = r.id")[0],
        "placas": uno("SELECT count(DISTINCT vehiculo_id) FROM remisiones r JOIN _ids_carga i ON i.id = r.id")[0],
        "productos": uno(
            "SELECT count(DISTINCT producto_id) FROM remision_productos p JOIN _ids_carga i ON i.id = p.remision_id"
        )[0],
        "lineas_por_estado": Counter(
            {
                e: n
                for e, n in session.exec(
                    text(
                        "SELECT r.estado_facturacion, count(p.id) FROM remisiones r JOIN _ids_carga i ON i.id = r.id "
                        "JOIN remision_productos p ON p.remision_id = r.id GROUP BY 1"
                    )
                ).all()
            }
        ),
        "prefijos": {
            p: (nl, nr)
            for p, nl, nr in session.exec(
                text(
                    "SELECT pf.codigo, count(p.id), count(DISTINCT r.id) FROM remisiones r JOIN _ids_carga i ON i.id = r.id "
                    "JOIN prefijos pf ON pf.id = r.prefijo_id LEFT JOIN remision_productos p ON p.remision_id = r.id GROUP BY 1 ORDER BY 1"
                )
            ).all()
        },
        "por_anio": {},
        "facturado_por_anio_factura": {},
    }
    for anio, material, flete, camabaja in session.exec(
        text(
            "SELECT extract(year FROM r.fecha)::int, sum(p.valor_material), sum(p.valor_flete), sum(p.valor_camabaja) "
            "FROM remisiones r JOIN _ids_carga i ON i.id = r.id JOIN remision_productos p ON p.remision_id = r.id GROUP BY 1 ORDER BY 1"
        )
    ).all():
        resultado["por_anio"][anio] = {"material": material or CERO, "flete": flete or CERO, "camabaja": camabaja or CERO, "facturado": CERO}
    for anio, facturado in session.exec(
        text(
            "SELECT extract(year FROM r.fecha)::int, sum(rf.valor_facturado) FROM remisiones r JOIN _ids_carga i ON i.id = r.id "
            "JOIN remision_facturacion rf ON rf.remision_id = r.id WHERE NOT rf.anulada GROUP BY 1"
        )
    ).all():
        resultado["por_anio"].setdefault(anio, {"material": CERO, "flete": CERO, "camabaja": CERO, "facturado": CERO})
        resultado["por_anio"][anio]["facturado"] = facturado or CERO
    for anio, facturado in session.exec(
        text(
            "SELECT extract(year FROM f.fecha_factura)::int, sum(rf.valor_facturado) FROM remision_facturacion rf "
            "JOIN _ids_carga i ON i.id = rf.remision_id JOIN facturas f ON f.id = rf.factura_id WHERE NOT rf.anulada GROUP BY 1 ORDER BY 1"
        )
    ).all():
        resultado["facturado_por_anio_factura"][anio] = facturado or CERO
    huerfanos = uno(
        "SELECT (SELECT count(*) FROM remision_productos p LEFT JOIN remisiones r ON r.id = p.remision_id WHERE r.id IS NULL),"
        " (SELECT count(*) FROM remision_facturacion rf LEFT JOIN remisiones r ON r.id = rf.remision_id WHERE r.id IS NULL),"
        " (SELECT count(*) FROM remision_facturacion rf LEFT JOIN facturas f ON f.id = rf.factura_id WHERE f.id IS NULL),"
        " (SELECT count(*) FROM facturas f WHERE NOT EXISTS (SELECT 1 FROM remision_facturacion rf WHERE rf.factura_id = f.id))"
    )
    resultado["huerfanos"] = {
        "líneas sin remisión": huerfanos[0],
        "facturaciones sin remisión": huerfanos[1],
        "facturaciones sin factura": huerfanos[2],
        "facturas sin remisiones": huerfanos[3],
    }
    session.rollback()  # suelta la tabla temporal
    return resultado
