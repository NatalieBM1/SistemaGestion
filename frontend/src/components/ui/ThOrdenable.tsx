import type { ReactNode, ThHTMLAttributes } from "react";
import type { Ordenamiento } from "../../hooks/useOrdenamiento";
import styles from "./Table.module.css";

interface ThOrdenableProps extends Omit<ThHTMLAttributes<HTMLTableCellElement>, "children"> {
  /** Nombre de la columna para el backend (o para ordenar en cliente). */
  campo: string;
  children: ReactNode;
  ordenamiento: Ordenamiento;
  onOrdenar: (campo: string) => void;
}

/** Encabezado de columna ordenable: clic o Enter/Espacio (es un <button>)
 * alterna ascendente → descendente → sin orden; flecha azul con el sentido
 * y `aria-sort` para lectores de pantalla. Lo usa `Table` y cualquier tabla
 * armada a mano. Las columnas de casillas y de Acciones van con un <th>
 * normal: no son ordenables. */
export function ThOrdenable({ campo, children, ordenamiento, onOrdenar, ...thProps }: ThOrdenableProps) {
  const sentido = ordenamiento.campo === campo ? ordenamiento.sentido : null;
  return (
    <th {...thProps} aria-sort={sentido === "asc" ? "ascending" : sentido === "desc" ? "descending" : "none"}>
      <button type="button" className={styles.thOrdenable} onClick={() => onOrdenar(campo)}>
        {children}
        <span className={styles.flechaOrden} aria-hidden="true">
          {sentido === "asc" ? "▲" : sentido === "desc" ? "▼" : ""}
        </span>
      </button>
    </th>
  );
}
