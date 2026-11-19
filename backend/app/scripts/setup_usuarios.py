"""Usuarios iniciales de una base LOCAL de desarrollo, leídos de un CSV privado.

Este archivo no contiene credenciales. Las lee de _privado/usuarios_iniciales.csv
(carpeta ignorada por git) o del CSV que se indique con --csv. Columnas:

    email,rol,password,nombre,unir_con_identificacion

- rol: admin | operador | consulta (roles Administrador, Operador, Solo Consulta).
- nombre: opcional si la cuenta ya existe o se une con un usuario histórico.
- unir_con_identificacion: opcional. Cédula de un usuario histórico (creador de
  remisiones del Excel, inactivo y sin acceso). Si se da, ese usuario se convierte
  en la cuenta activa (conserva su nombre, su cédula y sus remisiones) en vez de
  crear un duplicado. Nunca se une por parecido de nombre: solo por cédula.

Reglas:
- Se niega a correr con APP_ENV=production. En producción los usuarios se crean
  desde la app con contraseñas nuevas, fuertes y aleatorias.
- Valida todo antes de escribir: si una fila no sirve (correo, rol, contraseña de
  menos de 8 caracteres, cédula de unión que no existe) no se escribe nada.
- Cada cuenta queda con exactamente el rol indicado. Cambiar la contraseña cierra
  las sesiones abiertas de esa cuenta.
- Con --eliminar-otros: borra los usuarios que no están en el CSV (los históricos
  no se tocan). Si uno tiene registros a su nombre (remisiones, facturaciones,
  auditoría o cargas), no se borra: se desactiva y se informa.
- Nunca imprime contraseñas.

Uso (desde backend/, con DATABASE_URL de la base local):
    python -m app.scripts.setup_usuarios [--csv RUTA] [--eliminar-otros] [--simulacion]
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from pathlib import Path

from sqlalchemy import create_engine, func, text
from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import hash_password
from app.models.usuario import Rol, Usuario, UsuarioRol

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[3]
CSV_POR_DEFECTO = RAIZ / "_privado" / "usuarios_iniciales.csv"
ROLES = {"admin": "Administrador", "operador": "Operador", "consulta": "Solo Consulta"}
MIN_PASSWORD = 8  # misma regla que recuperar y cambiar la contraseña en la app
CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
REFERENCIAS = [
    ("remisiones", "usuario_creador_id"),
    ("remision_facturacion", "usuario_id"),
    ("auditoria", "usuario_id"),
    ("cargas_excel", "usuario_id"),
]


def _en_produccion() -> bool:
    return "production" in {(os.environ.get("APP_ENV") or "").strip().lower(), settings.app_env.strip().lower()}


def _leer_csv(ruta: Path) -> list[dict[str, str]]:
    if not ruta.exists():
        sys.exit(f"No existe el archivo de usuarios: {ruta}")
    with ruta.open(newline="", encoding="utf-8-sig") as f:
        filas = [{k.strip(): (v or "").strip() for k, v in fila.items()} for fila in csv.DictReader(f)]
    faltan = {"email", "rol", "password"} - set(filas[0] if filas else {})
    if faltan:
        sys.exit(f"Al CSV le faltan columnas: {', '.join(sorted(faltan))}")
    return filas


def main() -> int:
    p = argparse.ArgumentParser(description="Usuarios iniciales de desarrollo desde un CSV privado.")
    p.add_argument("--csv", type=Path, default=CSV_POR_DEFECTO)
    p.add_argument("--eliminar-otros", action="store_true", help="Borrar (o desactivar) los usuarios que no están en el CSV")
    p.add_argument("--simulacion", action="store_true", help="Mostrar lo que haría sin escribir")
    a = p.parse_args()

    if _en_produccion():
        sys.exit("Este script es solo para desarrollo y no corre con APP_ENV=production. "
                 "En producción crea los usuarios desde la app con contraseñas nuevas y aleatorias.")

    filas = _leer_csv(a.csv)
    url = os.environ.get("DATABASE_URL") or settings.database_url
    engine = create_engine(url.replace("postgres://", "postgresql://", 1))

    with Session(engine) as s:
        roles = {r.nombre: r for r in s.exec(select(Rol)).all()}
        errores: list[str] = []
        plan: list[tuple[dict[str, str], Usuario | None, Usuario | None]] = []
        correos_vistos: set[str] = set()
        for n, fila in enumerate(filas, start=2):
            email = fila["email"].lower()
            if not CORREO.match(email):
                errores.append(f"fila {n}: correo no válido")
                continue
            if email in correos_vistos:
                errores.append(f"fila {n}: {email} está repetido")
            correos_vistos.add(email)
            rol = ROLES.get(fila["rol"].lower())
            if rol is None:
                errores.append(f"fila {n} ({email}): rol «{fila['rol']}» no válido (admin, operador o consulta)")
            elif rol not in roles:
                errores.append(f"fila {n} ({email}): el rol {rol} no existe en la base (corre seed_auth)")
            if len(fila["password"]) < MIN_PASSWORD:
                errores.append(
                    f"fila {n} ({email}): la contraseña tiene menos de {MIN_PASSWORD} caracteres "
                    "(la app exige ese mínimo al recuperar o cambiar la contraseña)"
                )
            existente = s.exec(select(Usuario).where(func.lower(Usuario.email) == email)).first()
            historico = None
            cedula = fila.get("unir_con_identificacion", "")
            if cedula and existente is None:
                historico = s.exec(select(Usuario).where(Usuario.identificacion == cedula, Usuario.historico.is_(True))).first()
                if historico is None:
                    errores.append(f"fila {n} ({email}): no hay un usuario histórico con la cédula indicada para unir")
            if existente is None and historico is None and not fila.get("nombre"):
                errores.append(f"fila {n} ({email}): falta el nombre para crear la cuenta")
            plan.append((fila, existente, historico))
        if errores:
            print("No se escribió nada. Corrige el CSV:")
            for e in errores:
                print(f"  - {e}")
            return 1

        conservar: set[int] = set()
        for fila, existente, historico in plan:
            email = fila["email"].lower()
            rol = roles[ROLES[fila["rol"].lower()]]
            if existente is not None:
                usuario, accion = existente, "actualizada"
            elif historico is not None:
                usuario, accion = historico, f"unida con el usuario histórico id {historico.id} (conserva sus remisiones)"
                usuario.historico = False
            else:
                usuario = Usuario(nombre=fila["nombre"].upper(), email=email)
                accion = "creada"
            usuario.email = email
            if fila.get("nombre") and existente is None and historico is None:
                usuario.nombre = fila["nombre"].upper()
            usuario.password_hash = hash_password(fila["password"])
            usuario.activo = True
            # Cuentas de desarrollo: sin cambio obligatorio de contraseña.
            usuario.debe_cambiar_password = False
            usuario.token_version = (usuario.token_version or 0) + 1  # cierra sesiones abiertas
            s.add(usuario)
            s.flush()
            for ur in s.exec(select(UsuarioRol).where(UsuarioRol.usuario_id == usuario.id)).all():
                if ur.rol_id != rol.id:
                    s.delete(ur)
            if s.get(UsuarioRol, (usuario.id, rol.id)) is None:
                s.add(UsuarioRol(usuario_id=usuario.id, rol_id=rol.id))
            conservar.add(usuario.id)
            print(f"  {email}: cuenta {accion}, rol {rol.nombre}")

        if a.eliminar_otros:
            otros = s.exec(select(Usuario).where(Usuario.historico.is_(False))).all()
            for u in otros:
                if u.id in conservar:
                    continue
                refs = sum(
                    s.exec(text(f"SELECT count(*) FROM {tabla} WHERE {col} = :id").bindparams(id=u.id)).one()[0]
                    for tabla, col in REFERENCIAS
                )
                if refs:
                    u.activo = False
                    u.token_version = (u.token_version or 0) + 1
                    s.add(u)
                    print(f"  usuario id {u.id}: desactivado (tiene {refs} registros a su nombre; no se borra)")
                else:
                    for ur in s.exec(select(UsuarioRol).where(UsuarioRol.usuario_id == u.id)).all():
                        s.delete(ur)
                    s.flush()
                    s.delete(u)
                    print(f"  usuario id {u.id}: eliminado")

        if a.simulacion:
            s.rollback()
            print("Simulación: no se escribió nada.")
        else:
            s.commit()
            print("Listo. Las contraseñas no se muestran; están solo en el CSV privado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
