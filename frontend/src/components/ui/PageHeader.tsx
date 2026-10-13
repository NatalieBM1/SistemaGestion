import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { useOwnPageHeader } from "../../store/pageTitleStore";
import styles from "./PageHeader.module.css";

export type BreadcrumbItem = string | { label: string; to: string };

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  breadcrumb?: BreadcrumbItem[];
  actions?: ReactNode;
  children?: ReactNode;
}

export function PageHeader({ title, subtitle, breadcrumb, actions, children }: PageHeaderProps) {
  useOwnPageHeader();
  return (
    <div className={styles.root}>
      <header className={styles.head}>
        <div className={styles.text}>
          {breadcrumb && breadcrumb.length > 0 && (
            <nav className={styles.crumb} aria-label="Ruta de navegación">
              {breadcrumb.map((item, index) => (
                <span key={index}>
                  {index > 0 && "  /  "}
                  {typeof item === "string" ? (
                    item
                  ) : (
                    <Link to={item.to} className={styles.crumbLink}>
                      {item.label}
                    </Link>
                  )}
                </span>
              ))}
            </nav>
          )}
          <h1 className={styles.title}>{title}</h1>
          {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
        </div>
        {actions && <div className={styles.actions}>{actions}</div>}
      </header>
      <div className={styles.glow} aria-hidden="true" />
      {children}
    </div>
  );
}
