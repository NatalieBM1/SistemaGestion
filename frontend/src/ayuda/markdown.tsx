/** Lector de Markdown de la guía. Pequeño y propio: genera elementos de
 * React (nunca HTML crudo), así el contenido no puede inyectar código.
 *
 * Además del Markdown básico (##, ###, párrafos, listas, tablas, **negrita**,
 * *cursiva*, `código`, [enlaces](/ayuda/...)), entiende estos bloques:
 *
 *   :::pasos            lista numerada de pasos (líneas "1. ...")
 *   :::nota | :::importante | :::consejo   avisos
 *   :::campos           tabla de campos (Campo | Qué es | Obligatorio | Ejemplo)
 *   :::                 cierra el bloque
 *   @captura 01-nombre.png | qué debe mostrar
 */
import { Info, Lightbulb, TriangleAlert } from "lucide-react";
import { Fragment, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { Captura } from "./Captura";
import { separarAncla } from "./contenido";
import styles from "./Guia.module.css";

type Bloque =
  | { tipo: "titulo"; nivel: 2 | 3; texto: string; id: string }
  | { tipo: "parrafo"; texto: string }
  | { tipo: "lista"; ordenada: boolean; items: string[] }
  | { tipo: "tabla"; filas: string[][]; campos?: boolean }
  | { tipo: "pasos"; items: string[] }
  | { tipo: "aviso"; clase: "nota" | "importante" | "consejo"; bloques: Bloque[] }
  | { tipo: "captura"; archivo: string; descripcion: string };

const CELDAS = (linea: string) =>
  linea
    .trim()
    .replace(/^\||\|$/g, "")
    .split("|")
    .map((c) => c.trim());

export function analizar(texto: string): Bloque[] {
  const lineas = texto.replace(/\r\n/g, "\n").split("\n");
  const bloques: Bloque[] = [];
  let i = 0;
  while (i < lineas.length) {
    const linea = lineas[i];
    const directiva = linea.match(/^:::(pasos|nota|importante|consejo|campos)\s*$/);
    if (directiva) {
      const fin = lineas.indexOf(":::", i + 1);
      const interior = lineas.slice(i + 1, fin === -1 ? undefined : fin).join("\n");
      i = fin === -1 ? lineas.length : fin + 1;
      const tipo = directiva[1];
      if (tipo === "pasos") {
        bloques.push({
          tipo: "pasos",
          items: interior
            .split("\n")
            .filter((l) => /^\d+\.\s+/.test(l))
            .map((l) => l.replace(/^\d+\.\s+/, "")),
        });
      } else if (tipo === "campos") {
        const filas = interior
          .split("\n")
          .filter((l) => l.trim().startsWith("|") && !/^\|\s*-/.test(l.trim()))
          .map(CELDAS);
        bloques.push({ tipo: "tabla", filas, campos: true });
      } else {
        bloques.push({ tipo: "aviso", clase: tipo as "nota" | "importante" | "consejo", bloques: analizar(interior) });
      }
      continue;
    }
    const captura = linea.match(/^@captura\s+(\S+\.png)\s*\|\s*(.+)$/);
    if (captura) {
      bloques.push({ tipo: "captura", archivo: captura[1], descripcion: captura[2].trim() });
      i++;
      continue;
    }
    const titulo = linea.match(/^(#{2,3})\s+(.+)$/);
    if (titulo) {
      const { texto, id } = separarAncla(titulo[2]);
      bloques.push({ tipo: "titulo", nivel: titulo[1].length as 2 | 3, texto, id });
      i++;
      continue;
    }
    if (linea.trim().startsWith("|")) {
      const filas: string[][] = [];
      while (i < lineas.length && lineas[i].trim().startsWith("|")) {
        if (!/^\|\s*:?-/.test(lineas[i].trim())) filas.push(CELDAS(lineas[i]));
        i++;
      }
      bloques.push({ tipo: "tabla", filas });
      continue;
    }
    const item = linea.match(/^(\s*)([-*]|\d+\.)\s+(.+)$/);
    if (item) {
      const ordenada = /\d/.test(item[2]);
      const items: string[] = [];
      while (i < lineas.length) {
        const m = lineas[i].match(/^\s*([-*]|\d+\.)\s+(.+)$/);
        if (!m || /\d/.test(m[1]) !== ordenada) break;
        items.push(m[2]);
        i++;
      }
      bloques.push({ tipo: "lista", ordenada, items });
      continue;
    }
    if (linea.trim() === "") {
      i++;
      continue;
    }
    const parrafo: string[] = [];
    while (
      i < lineas.length &&
      lineas[i].trim() !== "" &&
      !/^(#{2,3}\s|:::|@captura|\||\s*([-*]|\d+\.)\s)/.test(lineas[i])
    ) {
      parrafo.push(lineas[i].trim());
      i++;
    }
    bloques.push({ tipo: "parrafo", texto: parrafo.join(" ") });
  }
  return bloques;
}

/** Negrita, cursiva, código y enlaces dentro de una línea. */
export function enLinea(texto: string): ReactNode[] {
  const partes: ReactNode[] = [];
  const patron = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\)|\*[^*]+\*)/g;
  let ultimo = 0;
  let clave = 0;
  for (const m of texto.matchAll(patron)) {
    if (m.index! > ultimo) partes.push(texto.slice(ultimo, m.index));
    const t = m[0];
    if (t.startsWith("**")) partes.push(<strong key={clave++}>{t.slice(2, -2)}</strong>);
    else if (t.startsWith("`")) partes.push(<code key={clave++}>{t.slice(1, -1)}</code>);
    else if (t.startsWith("[")) {
      const [, etiqueta, destino] = t.match(/^\[([^\]]+)\]\(([^)]+)\)$/)!;
      partes.push(
        destino.startsWith("/") || destino.startsWith("#") ? (
          <Link key={clave++} to={destino}>
            {etiqueta}
          </Link>
        ) : (
          <a key={clave++} href={destino} target="_blank" rel="noopener noreferrer">
            {etiqueta}
          </a>
        ),
      );
    } else partes.push(<em key={clave++}>{t.slice(1, -1)}</em>);
    ultimo = m.index! + t.length;
  }
  if (ultimo < texto.length) partes.push(texto.slice(ultimo));
  return partes;
}

const AVISOS = {
  nota: { titulo: "Nota", icono: <Info size={18} aria-hidden="true" /> },
  importante: { titulo: "Importante", icono: <TriangleAlert size={18} aria-hidden="true" /> },
  consejo: { titulo: "Consejo", icono: <Lightbulb size={18} aria-hidden="true" /> },
};

function Tabla({ filas, campos }: { filas: string[][]; campos?: boolean }) {
  const [cabecera, ...cuerpo] = filas;
  return (
    <div className={styles.tablaContenedor}>
      <table className={campos ? `${styles.tabla} ${styles.tablaCampos}` : styles.tabla}>
        {campos && <caption className={styles.srOnly}>Campos del formulario</caption>}
        <thead>
          <tr>
            {cabecera.map((c, i) => (
              <th key={i} scope="col">
                {enLinea(c)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {cuerpo.map((fila, i) => (
            <tr key={i}>
              {fila.map((c, j) => (
                <td key={j}>{enLinea(c)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Contenido({ bloques, seccion }: { bloques: Bloque[]; seccion: string }) {
  return (
    <>
      {bloques.map((b, i) => {
        switch (b.tipo) {
          case "titulo":
            return b.nivel === 2 ? (
              <h2 key={i} id={b.id} className={styles.h2}>
                {enLinea(b.texto)}
              </h2>
            ) : (
              <h3 key={i} id={b.id} className={styles.h3}>
                {enLinea(b.texto)}
              </h3>
            );
          case "parrafo":
            return <p key={i}>{enLinea(b.texto)}</p>;
          case "lista": {
            const Etiqueta = b.ordenada ? "ol" : "ul";
            return (
              <Etiqueta key={i} className={styles.lista}>
                {b.items.map((it, j) => (
                  <li key={j}>{enLinea(it)}</li>
                ))}
              </Etiqueta>
            );
          }
          case "tabla":
            return <Tabla key={i} filas={b.filas} campos={b.campos} />;
          case "pasos":
            return (
              <ol key={i} className={styles.pasos}>
                {b.items.map((it, j) => (
                  <li key={j}>
                    <span className={styles.pasoNumero} aria-hidden="true">
                      {j + 1}
                    </span>
                    <span>{enLinea(it)}</span>
                  </li>
                ))}
              </ol>
            );
          case "aviso":
            return (
              <aside key={i} className={`${styles.aviso} ${styles[`aviso_${b.clase}`]}`} aria-label={AVISOS[b.clase].titulo}>
                <div className={styles.avisoTitulo}>
                  {AVISOS[b.clase].icono}
                  {AVISOS[b.clase].titulo}
                </div>
                <Contenido bloques={b.bloques} seccion={seccion} />
              </aside>
            );
          case "captura":
            return <Captura key={i} seccion={seccion} archivo={b.archivo} descripcion={b.descripcion} />;
          default:
            return <Fragment key={i} />;
        }
      })}
    </>
  );
}

/** Texto plano (para el buscador). */
export function textoPlano(cuerpo: string): string {
  return cuerpo
    .replace(/^@captura\s+\S+\s*\|/gm, "")
    .replace(/^:::\w*/gm, "")
    .replace(/\{#[a-z0-9-]+\}/g, "")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/[*`#|>]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}
