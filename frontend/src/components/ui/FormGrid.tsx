import type { ReactNode } from "react";
import styles from "./FormGrid.module.css";

interface FormGridProps {
  columns?: 2 | 3 | 4;
  children: ReactNode;
}

/** Cuadrícula compacta para formularios: campos de 38 px (altura estándar de
 * `Input`/`AsyncSelect`), etiqueta encima, ícono a la izquierda y asterisco
 * azul en los obligatorios — todo ya resuelto por esos componentes. Este
 * contenedor solo define el número de columnas. Para que un campo ocupe más
 * de una columna, envuélvelo en un `<div>` con `grid-column: span N`. */
export function FormGrid({ columns = 2, children }: FormGridProps) {
  return <div className={styles.grid} style={{ "--form-grid-columns": columns } as React.CSSProperties}>{children}</div>;
}
