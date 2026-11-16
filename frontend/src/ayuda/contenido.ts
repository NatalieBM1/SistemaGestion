/** Carga las páginas de la guía (contenido/<seccion>/<pagina>.md) y su
 * encabezado. Todo esto vive en el bloque de carga diferida de /ayuda.
 *
 * Encabezado de cada .md (entre líneas ---):
 *   titulo: Nueva remisión
 *   descripcion: Cómo crear una remisión, pestaña por pestaña.
 *   orden: 2
 *   rol: todos | administrador
 *   actualizado: 2026-11-16
 */
import { SECCIONES } from "./secciones";

export interface Encabezado {
  nivel: 2 | 3;
  texto: string;
  id: string;
}

export interface Pagina {
  seccion: string;
  slug: string;
  ruta: string;
  titulo: string;
  descripcion: string;
  orden: number;
  soloAdministrador: boolean;
  actualizado: string;
  cuerpo: string;
  encabezados: Encabezado[];
}

const ARCHIVOS = import.meta.glob("./contenido/**/*.md", {
  query: "?raw",
  import: "default",
  eager: true,
}) as Record<string, string>;

export function slugify(texto: string): string {
  return texto
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

/** "## Pestaña Datos {#pestana-datos}" → texto y ancla explícita; si no
 * trae ancla, se genera del texto. */
export function separarAncla(texto: string): { texto: string; id: string } {
  const m = texto.match(/^(.*?)\s*\{#([a-z0-9-]+)\}\s*$/);
  return m ? { texto: m[1], id: m[2] } : { texto, id: slugify(texto) };
}

function leer(ruta: string, crudo: string): Pagina {
  const [, seccion, archivo] = ruta.match(/\.\/contenido\/([^/]+)\/([^/]+)\.md$/) ?? [];
  const m = crudo.replace(/\r\n/g, "\n").match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  const meta: Record<string, string> = {};
  let cuerpo = crudo;
  if (m) {
    for (const linea of m[1].split("\n")) {
      const i = linea.indexOf(":");
      if (i > 0) meta[linea.slice(0, i).trim()] = linea.slice(i + 1).trim();
    }
    cuerpo = m[2];
  }
  const encabezados: Encabezado[] = [];
  let enBloqueCodigo = false;
  for (const linea of cuerpo.split("\n")) {
    if (linea.startsWith("```")) enBloqueCodigo = !enBloqueCodigo;
    const h = !enBloqueCodigo && linea.match(/^(#{2,3})\s+(.+)$/);
    if (h) {
      const { texto, id } = separarAncla(h[2]);
      encabezados.push({ nivel: h[1].length as 2 | 3, texto, id });
    }
  }
  return {
    seccion,
    slug: archivo,
    ruta: `/ayuda/${seccion}/${archivo}`,
    titulo: meta.titulo ?? archivo,
    descripcion: meta.descripcion ?? "",
    orden: Number(meta.orden ?? 99),
    soloAdministrador: (meta.rol ?? "todos").toLowerCase() === "administrador",
    actualizado: meta.actualizado ?? "",
    cuerpo,
    encabezados,
  };
}

const ORDEN_SECCION = new Map(SECCIONES.map((s, i) => [s.slug, i]));

/** Todas las páginas, en el orden de lectura (sección, luego `orden`). */
export const PAGINAS: Pagina[] = Object.entries(ARCHIVOS)
  .map(([ruta, crudo]) => leer(ruta, crudo))
  .sort(
    (a, b) =>
      (ORDEN_SECCION.get(a.seccion) ?? 99) - (ORDEN_SECCION.get(b.seccion) ?? 99) ||
      a.orden - b.orden ||
      a.titulo.localeCompare(b.titulo, "es"),
  );

export function paginasDeSeccion(seccion: string): Pagina[] {
  return PAGINAS.filter((p) => p.seccion === seccion);
}

export function buscarPagina(seccion: string, slug?: string): Pagina | undefined {
  return slug ? PAGINAS.find((p) => p.seccion === seccion && p.slug === slug) : paginasDeSeccion(seccion)[0];
}
