/** Búsqueda de texto completo en el navegador (sin servidor). Compara sin
 * mayúsculas ni tildes; todas las palabras buscadas deben aparecer. Pesa
 * más que la palabra esté en el título o en un encabezado que en el texto. */
import { PAGINAS, type Pagina } from "./contenido";
import { textoPlano } from "./markdown";

const normalizar = (t: string) =>
  t.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

interface Entrada {
  pagina: Pagina;
  titulo: string;
  encabezados: string;
  texto: string;
  textoOriginal: string;
}

let indice: Entrada[] | null = null;

function construir(): Entrada[] {
  return PAGINAS.map((pagina) => {
    const original = textoPlano(pagina.cuerpo);
    return {
      pagina,
      titulo: normalizar(pagina.titulo + " " + pagina.descripcion),
      encabezados: normalizar(pagina.encabezados.map((e) => e.texto).join(" ")),
      texto: normalizar(original),
      textoOriginal: original,
    };
  });
}

export interface Resultado {
  pagina: Pagina;
  fragmento: string;
  ancla?: string;
}

export function buscar(consulta: string, limite = 12): Resultado[] {
  const palabras = normalizar(consulta).split(/\s+/).filter((p) => p.length >= 2);
  if (palabras.length === 0) return [];
  indice ??= construir();
  const puntuados: { r: Resultado; puntos: number }[] = [];
  for (const e of indice) {
    const todo = `${e.titulo} ${e.encabezados} ${e.texto}`;
    if (!palabras.every((p) => todo.includes(p))) continue;
    let puntos = 0;
    for (const p of palabras) {
      if (e.titulo.includes(p)) puntos += 10;
      if (e.encabezados.includes(p)) puntos += 4;
      puntos += Math.min(5, e.texto.split(p).length - 1);
    }
    const pos = e.texto.indexOf(palabras[0]);
    const desde = Math.max(0, pos - 60);
    const fragmento =
      pos >= 0
        ? (desde > 0 ? "…" : "") + e.textoOriginal.slice(desde, desde + 170).trim() + "…"
        : e.pagina.descripcion;
    const encabezado = e.pagina.encabezados.find((h) => normalizar(h.texto).includes(palabras[0]));
    puntuados.push({ r: { pagina: e.pagina, fragmento, ancla: encabezado?.id }, puntos });
  }
  return puntuados.sort((a, b) => b.puntos - a.puntos).slice(0, limite).map((x) => x.r);
}
