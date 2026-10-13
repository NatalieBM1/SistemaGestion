import type { AuthUser } from "../store/authStore";

/** GET /api/auth/me expone roles (nombres), no permisos exactos. El único
 * rol de solo lectura del backend se llama "Solo Consulta" (seed_auth.py);
 * nos apoyamos en ese nombre para decidir si el usuario puede escribir. */
export function canWrite(user: AuthUser | null): boolean {
  if (!user) return false;
  return !user.roles.includes("Solo Consulta");
}

/** Verifica un permiso granular real (ej. "usuarios.administrar"), a
 * diferencia de canWrite que solo distingue por nombre de rol. */
export function hasPermission(user: AuthUser | null, codigo: string): boolean {
  if (!user) return false;
  return user.permisos.includes(codigo);
}
