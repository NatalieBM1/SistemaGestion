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
