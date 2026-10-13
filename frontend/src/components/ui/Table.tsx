import { useState, type ReactNode, type UIEvent } from "react";
import styles from "./Table.module.css";

export interface TableColumn<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  monoData?: boolean;
  align?: "left" | "right";
  truncate?: boolean;
}

interface TableProps<T> {
  columns: TableColumn<T>[];
  data: T[];
  getRowId: (row: T) => string | number;
  isLoading?: boolean;
}

export function Table<T>({ columns, data, getRowId, isLoading }: TableProps<T>) {
  const [scrolled, setScrolled] = useState(false);

  const handleScroll = (event: UIEvent<HTMLDivElement>) => {
    setScrolled(event.currentTarget.scrollLeft > 0);
  };

  return (
    <div className={styles.wrapper} data-scrolled={scrolled} onScroll={handleScroll}>
      {isLoading && <span className={styles.srOnly} role="status">Cargando…</span>}
      <table className={styles.table}>
        <thead>
          <tr>
            {columns.map((column, index) => (
              <th
                key={column.key}
                className={[
                  column.align === "right" ? styles.alignRight : "",
                  index === 0 ? styles.stickyCol : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                {column.header}
              </th>
            ))}
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
              <tr key={getRowId(row)}>
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
