export type FieldType = "text" | "number" | "checkbox";

export interface CatalogoFieldConfig {
  name: string;
  label: string;
  type: FieldType;
  required?: boolean;
  monoData?: boolean;
}

export interface CatalogoColumnConfig {
  key: string;
  header: string;
  monoData?: boolean;
}

export interface CatalogoConfig {
  slug: string;
  endpoint: string;
  title: string;
  singular: string;
  searchPlaceholder: string;
  fields: CatalogoFieldConfig[];
  columns: CatalogoColumnConfig[];
}

export const CATALOGOS: Record<string, CatalogoConfig> = {
  prefijos: {
    slug: "prefijos",
    endpoint: "/api/catalogos/prefijos",
    title: "Prefijos",
    singular: "Prefijo",
    searchPlaceholder: "Buscar por código…",
    fields: [
      { name: "codigo", label: "Código", type: "text", required: true, monoData: true },
      { name: "consecutivo_actual", label: "Consecutivo actual", type: "number" },
      { name: "es_manual", label: "Es manual (remisión de papel)", type: "checkbox" },
    ],
    columns: [
      { key: "codigo", header: "Código", monoData: true },
      { key: "consecutivo_actual", header: "Consecutivo actual" },
      { key: "es_manual", header: "Es manual" },
    ],
  },
  formas_pago: {
    slug: "formas_pago",
    endpoint: "/api/catalogos/formas_pago",
    title: "Formas de pago",
    singular: "Forma de pago",
    searchPlaceholder: "Buscar por nombre…",
    fields: [{ name: "nombre", label: "Nombre", type: "text", required: true }],
    columns: [{ key: "nombre", header: "Nombre" }],
  },
  tipos_servicio: {
    slug: "tipos_servicio",
    endpoint: "/api/catalogos/tipos_servicio",
    title: "Tipos de servicio",
    singular: "Tipo de servicio",
    searchPlaceholder: "Buscar por nombre…",
    fields: [{ name: "nombre", label: "Nombre", type: "text", required: true }],
    columns: [{ key: "nombre", header: "Nombre" }],
  },
  productos: {
    slug: "productos",
    endpoint: "/api/catalogos/productos",
    title: "Productos",
    singular: "Producto",
    searchPlaceholder: "Buscar por nombre…",
    fields: [
      { name: "codigo", label: "Código", type: "text", monoData: true },
      { name: "nombre", label: "Nombre", type: "text", required: true },
    ],
    columns: [
      { key: "codigo", header: "Código", monoData: true },
      { key: "nombre", header: "Nombre" },
    ],
  },
  unidades_medida: {
    slug: "unidades_medida",
    endpoint: "/api/catalogos/unidades_medida",
    title: "Unidades de medida",
    singular: "Unidad de medida",
    searchPlaceholder: "Buscar por nombre…",
    fields: [{ name: "nombre", label: "Nombre", type: "text", required: true }],
    columns: [{ key: "nombre", header: "Nombre" }],
  },
  prefijos_factura: {
    slug: "prefijos_factura",
    endpoint: "/api/catalogos/prefijos_factura",
    title: "Prefijos de factura",
    singular: "Prefijo de factura",
    searchPlaceholder: "Buscar por código…",
    fields: [{ name: "codigo", label: "Código", type: "text", required: true, monoData: true }],
    columns: [{ key: "codigo", header: "Código", monoData: true }],
  },
  tipos_tercero: {
    slug: "tipos_tercero",
    endpoint: "/api/catalogos/tipos_tercero",
    title: "Tipos de tercero",
    singular: "Tipo de tercero",
    searchPlaceholder: "Buscar por nombre…",
    fields: [{ name: "nombre", label: "Nombre", type: "text", required: true }],
    columns: [{ key: "nombre", header: "Nombre" }],
  },
};

export const CATALOGO_ORDER = [
  "prefijos",
  "formas_pago",
  "tipos_servicio",
  "productos",
  "unidades_medida",
  "prefijos_factura",
  "tipos_tercero",
];
