/** Secciones de la guía, en el orden del menú lateral. El `slug` es el
 * nombre de la carpeta en contenido/ y en imagenes/. */
export interface Seccion {
  slug: string;
  titulo: string;
}

export const SECCIONES: Seccion[] = [
  { slug: "primeros-pasos", titulo: "Primeros pasos" },
  { slug: "dashboard", titulo: "Inicio (Dashboard)" },
  { slug: "remisiones", titulo: "Remisiones" },
  { slug: "facturacion", titulo: "Facturación" },
  { slug: "catalogos", titulo: "Catálogos" },
  { slug: "terceros", titulo: "Terceros" },
  { slug: "ubicaciones", titulo: "Ubicaciones" },
  { slug: "activos", titulo: "Activos" },
  { slug: "reportes", titulo: "Reportes" },
  { slug: "cargas-excel", titulo: "Cargas por Excel" },
  { slug: "administracion", titulo: "Administración" },
  { slug: "ayuda", titulo: "Preguntas y problemas" },
];
