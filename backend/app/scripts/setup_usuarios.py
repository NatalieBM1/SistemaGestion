"""Establece los tres usuarios del sistema con sus contraseñas y roles definidos.
Idempotente: crea el usuario si no existe, o actualiza su contraseña/nombre si ya existe.

Las contraseñas NO van en el código: se leen de variables de entorno
(SETUP_PASSWORD_ADMIN, SETUP_PASSWORD_OPERADOR, SETUP_PASSWORD_CONSULTA) y
no se imprimen.

Uso (desde backend/, con el venv activo y esas tres variables definidas):
    python -m app.scripts.setup_usuarios
"""

import os
import sys

from sqlmodel import Session, select

from app.core.database import engine
from app.core.security import hash_password
from app.models.usuario import Rol, Usuario, UsuarioRol

USUARIOS = [
    {
        "email": "admin@transportesguerrero.com",
        "nombre": "Administrador del Sistema",
        "password_env": "SETUP_PASSWORD_ADMIN",
        "rol": "Administrador",
    },
    {
        "email": "operador@transportesguerrero.com",
        "nombre": "Operador Principal",
        "password_env": "SETUP_PASSWORD_OPERADOR",
        "rol": "Operador",
    },
    {
        "email": "consulta@transportesguerrero.com",
        "nombre": "Consulta Principal",
        "password_env": "SETUP_PASSWORD_CONSULTA",
        "rol": "Solo Consulta",
    },
]


def main() -> None:
    faltan = [d["password_env"] for d in USUARIOS if not os.environ.get(d["password_env"])]
    if faltan:
        sys.exit(f"Faltan variables de entorno con las contraseñas: {', '.join(faltan)}")
    for datos in USUARIOS:
        datos["password"] = os.environ[datos["password_env"]]

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

    print("\nUsuarios configurados correctamente (contraseñas tomadas de las variables de entorno).")


if __name__ == "__main__":
    main()
