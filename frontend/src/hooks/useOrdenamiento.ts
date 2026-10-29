import { useState } from "react";

export type Sentido = "asc" | "desc";

export interface Ordenamiento {
  campo: string | null;
  sentido: Sentido | null;
}

/** Clic en un encabezado alterna ascendente → descendente → sin orden
 * (vuelve al orden por defecto de la lista). Clic en una columna distinta
 * arranca en ascendente. */
export function useOrdenamiento(inicial: Ordenamiento = { campo: null, sentido: null }) {
  const [ordenamiento, setOrdenamiento] = useState<Ordenamiento>(inicial);

  const alternar = (campo: string) => {
    setOrdenamiento((actual) => {
      if (actual.campo !== campo) return { campo, sentido: "asc" };
      if (actual.sentido === "asc") return { campo, sentido: "desc" };
      return { campo: null, sentido: null };
    });
  };

  return { ordenamiento, alternar };
}

type ValorOrdenable = string | number | null | undefined;

const comparadorTexto = new Intl.Collator("es-CO", { numeric: true, sensitivity: "base" });

/** Orden en cliente, para listas que se cargan completas (sin paginar en
 * el servidor). `valores` dice qué valor comparar por columna: números se
 * comparan como números; textos en español y con `numeric` (así
 * "GTM-9" < "GTM-10" y "F-7-468" < "F-7-1000"); fechas ISO (yyyy-mm-dd)
 * ya ordenan bien como texto. Vacíos siempre al final. Sin orden activo
 * devuelve la lista tal cual (el orden por defecto). */
export function ordenarEnCliente<T>(
  items: T[],
  ordenamiento: Ordenamiento,
  valores: Record<string, (item: T) => ValorOrdenable>,
): T[] {
  const { campo, sentido } = ordenamiento;
  const valor = campo ? valores[campo] : undefined;
  if (!valor || !sentido) return items;
  const signo = sentido === "asc" ? 1 : -1;
  return [...items].sort((a, b) => {
    const va = valor(a);
    const vb = valor(b);
    const vacioA = va == null || va === "";
    const vacioB = vb == null || vb === "";
    if (vacioA || vacioB) return vacioA === vacioB ? 0 : vacioA ? 1 : -1;
    if (typeof va === "number" && typeof vb === "number") return signo * (va - vb);
    return signo * comparadorTexto.compare(String(va), String(vb));
  });
}
