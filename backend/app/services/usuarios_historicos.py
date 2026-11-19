"""Activar un usuario histórico (creador de remisiones del Excel, inactivo y sin
acceso) como cuenta real, sin duplicarlo: conserva su nombre, su cédula y sus
remisiones.

La contraseña la genera el sistema (aleatoria), se devuelve UNA sola vez a quien
hace la activación y la persona debe cambiarla al primer ingreso. Nunca se lee
de un archivo ni se guarda en claro. Lo usan:
- la API  POST /api/admin/usuarios/historicos/activar  (pantalla Usuarios), y
- el comando  python -m app.scripts.activar_usuario_historico.
"""

from __future__ import annotations

import re
import secrets
import string

from fastapi import HTTPException, status
from sqlmodel import Session, func, select

from app.core.security import hash_password
from app.models.auditoria import Auditoria
from app.models.usuario import Rol, Usuario, UsuarioRol

ROLES = {"admin": "Administrador", "operador": "Operador", "consulta": "Solo Consulta"}
_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_ALFABETO = string.ascii_letters + string.digits
LARGO_PASSWORD = 16


def generar_password_temporal(largo: int = LARGO_PASSWORD) -> str:
    """Aleatoria (módulo secrets), con mayúsculas, minúsculas y números."""
    while True:
        clave = "".join(secrets.choice(_ALFABETO) for _ in range(largo))
        if any(c.islower() for c in clave) and any(c.isupper() for c in clave) and any(c.isdigit() for c in clave):
            return clave


def _nombre_rol(rol: str) -> str:
    valor = (rol or "").strip()
    if valor.lower() in ROLES:
        return ROLES[valor.lower()]
    if valor in ROLES.values():
        return valor
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="Rol no válido: usa Administrador, Operador o Solo Consulta.",
    )


def activar_usuario_historico(
    session: Session, *, identificacion: str, email: str, rol: str, actor_id: int | None = None
) -> tuple[Usuario, str]:
    """Devuelve (usuario, contraseña temporal). La contraseña no se guarda en
    claro ni se registra en ningún lado: quien llama la muestra una sola vez."""
    identificacion = (identificacion or "").strip()
    email = (email or "").strip().lower()
    if not identificacion:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Falta la identificación.")
    if not _CORREO.match(email):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="El correo no es válido.")
    nombre_rol = _nombre_rol(rol)

    usuario = session.exec(
        select(Usuario).where(Usuario.identificacion == identificacion, Usuario.historico.is_(True))
    ).first()
    if usuario is None:
        activa = session.exec(select(Usuario.id).where(Usuario.identificacion == identificacion)).first()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT if activa else status.HTTP_404_NOT_FOUND,
            detail=(
                "Esa identificación ya pertenece a una cuenta activa: no es un usuario histórico."
                if activa
                else "No hay un usuario histórico con esa identificación."
            ),
        )
    if session.exec(select(Usuario.id).where(func.lower(Usuario.email) == email, Usuario.id != usuario.id)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Ya existe un usuario con el correo '{email}'.")
    rol_obj = session.exec(select(Rol).where(Rol.nombre == nombre_rol)).first()
    if rol_obj is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"El rol {nombre_rol} no existe.")

    password = generar_password_temporal()
    usuario.email = email
    usuario.password_hash = hash_password(password)
    usuario.activo = True
    usuario.historico = False
    usuario.debe_cambiar_password = True
    usuario.token_version = (usuario.token_version or 0) + 1
    session.add(usuario)
    for ur in session.exec(select(UsuarioRol).where(UsuarioRol.usuario_id == usuario.id)).all():
        if ur.rol_id != rol_obj.id:
            session.delete(ur)
    if session.get(UsuarioRol, (usuario.id, rol_obj.id)) is None:
        session.add(UsuarioRol(usuario_id=usuario.id, rol_id=rol_obj.id))
    session.add(
        Auditoria(
            tabla="usuarios",
            registro_id=usuario.id,
            accion="ACTIVAR_HISTORICO",
            usuario_id=actor_id,
            detalle_json={"email": email, "rol": nombre_rol},  # nunca la contraseña
        )
    )
    session.commit()
    session.refresh(usuario)
    return usuario, password
