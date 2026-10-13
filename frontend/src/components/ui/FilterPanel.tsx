import type { ReactNode } from "react";
import styles from "./FilterPanel.module.css";

interface FilterPanelProps {
  search?: ReactNode;
  children?: ReactNode;
  footer?: ReactNode;
}

export function FilterPanel({ search, children, footer }: FilterPanelProps) {
  return (
    <section className={styles.panel} aria-label="Filtros">
      {search && <div className={styles.search}>{search}</div>}
      {children && <div className={styles.fields}>{children}</div>}
      {footer && <div className={styles.footer}>{footer}</div>}
    </section>
  );
}
