import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { hasPermission } from "../lib/permissions";
import { useAuthStore } from "../store/authStore";

interface RequirePermissionProps {
  permiso: string;
  children: ReactNode;
}

/** Protege una ruta detrás de un permiso granular (no solo autenticación).
 * Se usa dentro de ProtectedRoute, que ya garantiza que hay sesión activa.
 * Si el usuario no tiene el permiso, redirige a /acceso-denegado con un
 * mensaje claro en vez de dejar pasar o mostrar un error crudo del backend. */
export function RequirePermission({ permiso, children }: RequirePermissionProps) {
  const user = useAuthStore((state) => state.user);
  const location = useLocation();

  if (!hasPermission(user, permiso)) {
    return (
      <Navigate
        to="/acceso-denegado"
        replace
        state={{ permisoRequerido: permiso, rutaOriginal: location.pathname }}
      />
    );
  }

  return children;
}
