/** Formato de números y moneda para Colombia (es-CO), único en toda la
 * interfaz y en lo impreso. Los reportes Excel NO usan esto: ahí las celdas
 * siguen siendo numéricas para poder reimportarlas.
 *
 * `useGrouping: "always"`: en es-CO el navegador por defecto no separa los
 * números de 4 cifras ("1234"); el cliente los quiere como "1.234". */

type NumeroEntrada = string | number | null | undefined;

const CANTIDAD = new Intl.NumberFormat("es-CO", {
  maximumFractionDigits: 3,
  useGrouping: "always",
});
const PESOS_ENTEROS = new Intl.NumberFormat("es-CO", {
  maximumFractionDigits: 0,
  useGrouping: "always",
});
const PESOS_CON_CENTAVOS = new Intl.NumberFormat("es-CO", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
  useGrouping: "always",
});

function aNumero(valor: NumeroEntrada): number | null {
  if (valor == null || valor === "") return null;
  const n = typeof valor === "number" ? valor : Number(valor);
  return Number.isFinite(n) ? n : null;
}

/** Cantidades, kilómetros, viajes, conteos: sin ceros finales y con coma
 * decimal. "1.000" (de la API) → "1", "145.000" → "145", 1.5 → "1,5",
 * 12500 → "12.500". Vacío si no hay dato. */
export function formatCantidad(valor: NumeroEntrada): string {
  const n = aNumero(valor);
  return n == null ? (valor == null ? "" : String(valor)) : CANTIDAD.format(n);
}

/** Pesos colombianos: "$ 1.234.567"; con centavos, "$ 1.234.567,50"
 * (máximo 2 decimales). Vacío si no hay dato. */
export function formatCOP(valor: NumeroEntrada): string {
  const n = aNumero(valor);
  if (n == null) return valor == null ? "" : String(valor);
  const redondeado = Math.round(n * 100) / 100;
  const absoluto = Math.abs(redondeado);
  const tieneCentavos = Math.round(absoluto * 100) % 100 !== 0;
  const texto = (tieneCentavos ? PESOS_CON_CENTAVOS : PESOS_ENTEROS).format(absoluto);
  return `${redondeado < 0 ? "-" : ""}$ ${texto}`;
}

/** Unidad de medida para mostrar: "Metro cúbico" (con o sin mayúsculas,
 * tildes o plural) se ve "m³"; el resto queda igual. Solo presentación: el
 * nombre del catálogo y los reportes Excel no cambian. */
export function formatUnidad(nombre: string | null | undefined): string {
  if (!nombre) return "";
  const normal = nombre.normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toLowerCase();
  return /^(metros? cubicos?|m3|m³)$/.test(normal) ? "m³" : nombre;
}

/** Lee lo que el usuario escribe en un campo numérico en formato es-CO:
 * coma decimal y punto de miles ("1.234,5" → "1234.5"). Si trae un solo
 * punto y no hay coma ("1.5"), el punto se toma como decimal. Devuelve el
 * texto normalizado para la API ("" si queda vacío) o null si no es número. */
export function parseNumeroEsCO(texto: string): string | null {
  let limpio = texto.replace(/\s|\$/g, "");
  if (limpio === "") return "";
  if (limpio.includes(",")) {
    limpio = limpio.replace(/\./g, "").replace(",", ".");
  } else if ((limpio.match(/\./g) ?? []).length > 1 || /^\d{1,3}(\.\d{3})+$/.test(limpio)) {
    // "12.500" o "1.234.567": puntos de miles.
    limpio = limpio.replace(/\./g, "");
  }
  return /^-?\d*\.?\d*$/.test(limpio) && limpio !== "-" && limpio !== "." ? limpio : null;
}
