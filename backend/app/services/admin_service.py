"""Reglas de negocio de Administración. Aislada para que la única regla
delicada de este módulo —no dejar el sistema sin nadie que pueda
administrarlo— viva en un solo lugar, en vez de repetirse a mano en cada
endpoint que podría romperla.
"""

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.usuario import Permiso, RolPermiso, Usuario, UsuarioRol

ADMIN_PERMISO = "usuarios.administrar"

MENSAJE_SIN_ADMINISTRADOR = (
    "No se puede completar esta acción: dejaría el sistema sin ningún "
    "usuario con permiso para administrar usuarios y roles."
)


def validar_no_deja_sistema_sin_administrador(
    session: Session,
    *,
    excluir_usuario_rol: tuple[int, int] | None = None,
    excluir_rol_permiso: tuple[int, int] | None = None,
    excluir_usuario_id: int | None = None,
) -> None:
    """Simula la operación que se está por ejecutar (quitar un rol a un
    usuario, quitar un permiso a un rol, o desactivar un usuario) y verifica
    que, después de aplicarla, siga existiendo al menos un usuario activo
    que tenga 'usuarios.administrar' por al menos uno de sus roles.

    Se pasa como mucho una de las tres exclusiones, según cuál de las tres
    operaciones se esté validando; cada una filtra de la consulta
    exactamente la fila que la operación en curso eliminaría, para no tener
    que materializar listas en Python y comparar antes/después.
    """
    statement = (
        select(Usuario.id)
        .join(UsuarioRol, UsuarioRol.usuario_id == Usuario.id)
        .join(RolPermiso, RolPermiso.rol_id == UsuarioRol.rol_id)
        .join(Permiso, Permiso.id == RolPermiso.permiso_id)
        .where(Permiso.codigo == ADMIN_PERMISO, Usuario.activo.is_(True))
    )

    if excluir_usuario_rol is not None:
        usuario_id, rol_id = excluir_usuario_rol
        statement = statement.where(
            ~((UsuarioRol.usuario_id == usuario_id) & (UsuarioRol.rol_id == rol_id))
        )

    if excluir_rol_permiso is not None:
        rol_id, permiso_id = excluir_rol_permiso
        statement = statement.where(
            ~((UsuarioRol.rol_id == rol_id) & (RolPermiso.permiso_id == permiso_id))
        )

    if excluir_usuario_id is not None:
        statement = statement.where(Usuario.id != excluir_usuario_id)

    quedaria_alguien = session.exec(statement.limit(1)).first() is not None
    if not quedaria_alguien:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=MENSAJE_SIN_ADMINISTRADOR,
        )
