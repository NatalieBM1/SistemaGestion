"""Establece los tres usuarios del sistema con sus contraseñas y roles definidos.
Idempotente: crea el usuario si no existe, o actualiza su contraseña/nombre si ya existe.

Uso: python -m app.scripts.setup_usuarios (desde backend/, con el venv activo)
"""

from sqlmodel import Session, select

from app.core.database import engine
from app.core.security import hash_password
from app.models.usuario import Rol, Usuario, UsuarioRol

USUARIOS = [
    {
        "email": "admin@transportesguerrero.com",
        "nombre": "Administrador del Sistema",
        "password": "Administrador2026!",
        "rol": "Administrador",
    },
    {
        "email": "operador@transportesguerrero.com",
        "nombre": "Operador Principal",
        "password": "Operador2026!",
        "rol": "Operador",
    },
    {
        "email": "consulta@transportesguerrero.com",
        "nombre": "Consulta Principal",
        "password": "Consulta2026!",
        "rol": "Solo Consulta",
    },
]


def main() -> None:
    with Session(engine) as session:
        for datos in USUARIOS:
            # Obtener el rol correspondiente
            rol = session.exec(select(Rol).where(Rol.nombre == datos["rol"])).first()
            if rol is None:
                print(f"  ERROR: Rol '{datos['rol']}' no encontrado. Ejecuta seed_auth primero.")
                continue

            # Buscar o crear el usuario
            usuario = session.exec(
                select(Usuario).where(Usuario.email == datos["email"])
            ).first()

            if usuario is None:
                usuario = Usuario(
                    nombre=datos["nombre"],
                    email=datos["email"],
                    password_hash=hash_password(datos["password"]),
                    activo=True,
                )
                session.add(usuario)
                session.flush()
                accion = "Creado"
            else:
                usuario.nombre = datos["nombre"]
                usuario.password_hash = hash_password(datos["password"])
                usuario.token_version += 1
                usuario.activo = True
                session.add(usuario)
                session.flush()
                accion = "Actualizado"

            # Asignar el rol si no lo tiene
            if session.get(UsuarioRol, (usuario.id, rol.id)) is None:
                session.add(UsuarioRol(usuario_id=usuario.id, rol_id=rol.id))

            session.commit()
            print(f"  {accion}: {datos['email']} ({datos['rol']})")

    print("\nUsuarios configurados correctamente.")
    print("  admin@transportesguerrero.com  — Administrador2026!")
    print("  operador@transportesguerrero.com — Operador2026!")
    print("  consulta@transportesguerrero.com — Consulta2026!")


if __name__ == "__main__":
    main()
