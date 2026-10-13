import { useEffect } from "react";
import { useLocation } from "react-router-dom";

const NOMBRE_EMPRESA = "Transportes G&G";

const SECCIONES: { prefijo: string; titulo: string }[] = [
  { prefijo: "/login", titulo: "Iniciar sesión" },
  { prefijo: "/remisiones", titulo: "Remisiones" },
  { prefijo: "/facturas", titulo: "Facturación" },
  { prefijo: "/terceros", titulo: "Terceros" },
  { prefijo: "/ubicaciones", titulo: "Ubicaciones" },
  { prefijo: "/activos", titulo: "Activos" },
  { prefijo: "/catalogos", titulo: "Catálogos" },
  { prefijo: "/reportes", titulo: "Reportes" },
  { prefijo: "/admin/usuarios", titulo: "Usuarios" },
  { prefijo: "/admin/roles", titulo: "Roles" },
  { prefijo: "/acceso-denegado", titulo: "Acceso denegado" },
];

function tituloDeRuta(pathname: string): string | null {
  if (pathname === "/") return "Inicio";
  const seccion = SECCIONES.find((s) => pathname.startsWith(s.prefijo));
  return seccion?.titulo ?? null;
}

/** Mantiene el título de la pestaña del navegador sincronizado con la
 * sección actual (ej. "Remisiones · Transportes G&G"). No renderiza nada. */
export function DocumentTitle() {
  const { pathname } = useLocation();

  useEffect(() => {
    const titulo = tituloDeRuta(pathname);
    document.title = titulo ? `${titulo} · ${NOMBRE_EMPRESA}` : NOMBRE_EMPRESA;
  }, [pathname]);

  return null;
}
