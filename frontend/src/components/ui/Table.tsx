import { useState, type ReactNode, type UIEvent } from "react";
import type { Ordenamiento } from "../../hooks/useOrdenamiento";
import { ThOrdenable } from "./ThOrdenable";
import styles from "./Table.module.css";

export interface TableColumn<T> {
  key: string;
  header: ReactNode;
  render: (row: T) => ReactNode;
  monoData?: boolean;
  align?: "left" | "right";
  truncate?: boolean;
  /** Si se da, el encabezado se vuelve un botón ordenable (clic o
   * Enter/Espacio alterna ascendente → descendente → sin orden). Este es
   * el nombre de columna que se manda al backend (o se usa para ordenar
   * en cliente), no necesariamente igual a `key`. */
  sortField?: string;
}

interface TableProps<T> {
  columns: TableColumn<T>[];
  data: T[];
  getRowId: (row: T) => string | number;
  isLoading?: boolean;
  /** Clases extra por fila, ej. para resaltar seleccionadas o atenuar
   * las que no se pueden tocar (se concatenan con las de la celda). */
  getRowClassName?: (row: T) => string | undefined;
  /** Bloque A: ordenamiento activo + callback al hacer clic en una
   * columna con `sortField`. Viene de `useOrdenamiento()`. */
  ordenamiento?: Ordenamiento;
  onOrdenar?: (campo: string) => void;
  /** Sin ancho mínimo, para tablas dentro de paneles angostos. */
  compacta?: boolean;
}

export function Table<T>({
  columns,
  data,
  getRowId,
  isLoading,
  getRowClassName,
  ordenamiento,
  onOrdenar,
  compacta,
}: TableProps<T>) {
  const [scrolled, setScrolled] = useState(false);

  const handleScroll = (event: UIEvent<HTMLDivElement>) => {
    setScrolled(event.currentTarget.scrollLeft > 0);
  };

  return (
    <div className={styles.wrapper} data-scrolled={scrolled} onScroll={handleScroll}>
      {isLoading && <span className={styles.srOnly} role="status">Cargando…</span>}
      <table className={compacta ? `${styles.table} ${styles.tableCompacta}` : styles.table}>
        <thead>
          <tr>
            {columns.map((column, index) => {
              const className =
                [column.align === "right" ? styles.alignRight : "", index === 0 ? styles.stickyCol : ""]
                  .filter(Boolean)
                  .join(" ") || undefined;
              return column.sortField && onOrdenar ? (
                <ThOrdenable
                  key={column.key}
                  campo={column.sortField}
                  ordenamiento={ordenamiento ?? { campo: null, sentido: null }}
                  onOrdenar={onOrdenar}
                  className={className}
                >
                  {column.header}
                </ThOrdenable>
              ) : (
                <th key={column.key} className={className}>
                  {column.header}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {isLoading ? (
            [...Array(6)].map((_, rowIndex) => (
              <tr key={rowIndex} className={styles.skeletonRow} aria-hidden="true">
                {columns.map((column, index) => (
                  <td key={column.key} className={index === 0 ? styles.stickyCol : undefined}>
                    <div className={styles.skeletonBar} style={{ width: `${55 + ((rowIndex * 13 + index * 17) % 35)}%` }} />
                  </td>
                ))}
              </tr>
            ))
          ) : (
            data.map((row) => (
              <tr key={getRowId(row)} className={getRowClassName?.(row)}>
                {columns.map((column, index) => {
                  const content = column.render(row);
                  return (
                    <td
                      key={column.key}
                      className={[
                        column.align === "right" ? styles.alignRight : "",
                        column.monoData ? "font-mono-data" : "",
                        index === 0 ? styles.stickyCol : "",
                        column.truncate ? styles.truncateCell : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                    >
                      {column.truncate ? (
                        <div className={styles.truncate} title={typeof content === "string" ? content : undefined}>
                          {content}
                        </div>
                      ) : (
                        content
                      )}
                    </td>
                  );
                })}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
