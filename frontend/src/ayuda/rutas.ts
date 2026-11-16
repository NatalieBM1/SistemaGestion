/** Página de la guía de usuario que corresponde a cada pantalla. Este
 * archivo NO carga la guía (es liviano): solo arma los enlaces del botón
 * "Documentación". La guía se descarga aparte al abrir /ayuda. */
export const AYUDA = {
  inicio: "/ayuda",
  dashboard: "/ayuda/dashboard",
  remisiones: "/ayuda/remisiones",
  remisionFormulario: "/ayuda/remisiones/nueva-remision",
  facturacion: "/ayuda/facturacion",
  detalleFactura: "/ayuda/facturacion/detalle-factura",
  cargasExcel: "/ayuda/cargas-excel",
  catalogos: "/ayuda/catalogos",
  terceros: "/ayuda/terceros",
  ubicaciones: "/ayuda/ubicaciones",
  activos: "/ayuda/activos",
  reportes: "/ayuda/reportes",
  usuarios: "/ayuda/administracion/usuarios",
  roles: "/ayuda/administracion/roles",
} as const;

/** Catálogo (slug de la ruta /catalogos/<slug>) → página de la guía. */
export const AYUDA_CATALOGOS: Record<string, string> = {
  prefijos: "/ayuda/catalogos/prefijos",
  formas_pago: "/ayuda/catalogos/formas-de-pago",
  tipos_servicio: "/ayuda/catalogos/tipos-de-servicio",
  productos: "/ayuda/catalogos/productos",
  unidades_medida: "/ayuda/catalogos/unidades-de-medida",
  prefijos_factura: "/ayuda/catalogos/prefijos-de-factura",
  tipos_tercero: "/ayuda/catalogos/tipos-de-tercero",
};

/** Pestaña del formulario de remisión → ancla de su sección en la guía. */
export const ANCLAS_REMISION: Record<string, string> = {
  datos: "pestana-datos",
  productos: "pestana-productos",
  facturacion: "pestana-facturacion",
};
