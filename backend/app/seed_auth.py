"""Inserta el catálogo de permisos, los 3 roles base y el usuario administrador
inicial. Idempotente: se puede correr varias veces sin duplicar ni fallar.

Uso: python -m app.seed_auth (desde backend/, con el venv activo)
"""

from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import engine
from app.core.security import hash_password
from app.models.usuario import Permiso, Rol, RolPermiso, Usuario, UsuarioRol

PERMISOS = [
    ("catalogos.leer", "catalogos"),
    ("catalogos.escribir", "catalogos"),
    # Separados de "catalogos.escribir" para que el rol Operador pueda
    # crear registros en los catálogos (prefijos, formas de pago, tipos de
    # servicio, productos, unidades de medida, prefijos de factura, tipos
    # de tercero) pero no editarlos ni borrarlos. "catalogos.escribir"
    # sigue gobernando Proyectos, que no entra en esta restricción.
    ("catalogos.crear", "catalogos"),
    ("catalogos.editar", "catalogos"),
    ("catalogos.eliminar", "catalogos"),
    # Prefijos es más restrictivo que el resto de catálogos: solo
    # Administrador puede crear/editar/eliminar (ni siquiera Operador
    # puede crear uno nuevo, a diferencia de los otros 6 catálogos).
    ("prefijos.administrar", "catalogos"),
    ("terceros.leer", "terceros"),
    ("terceros.escribir", "terceros"),
    ("ubicaciones.leer", "ubicaciones"),
    ("ubicaciones.escribir", "ubicaciones"),
    ("activos.leer", "activos"),
    ("activos.escribir", "activos"),
    ("remisiones.leer", "remisiones"),
    ("remisiones.escribir", "remisiones"),
    ("remisiones.actualizar_nit", "remisiones"),
    ("facturas.leer", "facturas"),
    ("facturas.escribir", "facturas"),
    ("usuarios.administrar", "usuarios"),
]

PERMISOS_OPERADOR = [
    "catalogos.leer",
    "catalogos.escribir",  # cubre Proyectos (crear/editar/eliminar), no restringido
    "catalogos.crear",  # crear en el resto de catálogos; NO editar.catalogos / eliminar.catalogos
    "terceros.leer",
    "terceros.escribir",
    "ubicaciones.leer",
    "ubicaciones.escribir",
    "activos.leer",
    "activos.escribir",
    "remisiones.leer",
    "remisiones.escribir",
    "remisiones.actualizar_nit",
    "facturas.leer",
    "facturas.escribir",
]

PERMISOS_SOLO_CONSULTA = [
    "catalogos.leer",
    "terceros.leer",
    "ubicaciones.leer",
    "activos.leer",
    "remisiones.leer",
    "facturas.leer",
]

ADMIN_EMAIL = "admin@transportesguerrero.com"


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


def _asignar_permisos_a_rol(session: Session, rol: Rol, permisos: list[Permiso]) -> None:
    for permiso in permisos:
        if session.get(RolPermiso, (rol.id, permiso.id)) is None:
            session.add(RolPermiso(rol_id=rol.id, permiso_id=permiso.id))


def seed(session: Session) -> None:
    permisos_por_codigo: dict[str, Permiso] = {}
    for codigo, modulo in PERMISOS:
        permisos_por_codigo[codigo] = _obtener_o_crear(
            session, Permiso, codigo=codigo, defaults={"modulo": modulo}
        )
    session.flush()

    rol_admin = _obtener_o_crear(session, Rol, nombre="Administrador")
    _asignar_permisos_a_rol(session, rol_admin, list(permisos_por_codigo.values()))

    rol_operador = _obtener_o_crear(session, Rol, nombre="Operador")
    _asignar_permisos_a_rol(
        session, rol_operador, [permisos_por_codigo[c] for c in PERMISOS_OPERADOR]
    )

    rol_consulta = _obtener_o_crear(session, Rol, nombre="Solo Consulta")
    _asignar_permisos_a_rol(
        session, rol_consulta, [permisos_por_codigo[c] for c in PERMISOS_SOLO_CONSULTA]
    )

    usuario_admin = _obtener_o_crear(
        session,
        Usuario,
        email=ADMIN_EMAIL,
        defaults={
            "nombre": "Administrador del Sistema",
            "password_hash": hash_password(settings.admin_initial_password),
            "activo": True,
        },
    )
    session.flush()
    if session.get(UsuarioRol, (usuario_admin.id, rol_admin.id)) is None:
        session.add(UsuarioRol(usuario_id=usuario_admin.id, rol_id=rol_admin.id))

    session.commit()


def main() -> None:
    with Session(engine) as session:
        seed(session)
    print("Roles, permisos y usuario administrador insertados (o ya existentes).")
    print(f"Usuario administrador: {ADMIN_EMAIL}")
    print("Contraseña: la que hayas puesto en ADMIN_INITIAL_PASSWORD en tu .env.")
    print("Si la cuenta ya existía, esta contraseña NO se tocó. Cámbiala desde la app si es nueva.")


if __name__ == "__main__":
    main()
