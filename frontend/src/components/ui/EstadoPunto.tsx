import styles from "./EstadoPunto.module.css";

type EstadoColor = "success" | "warning" | "danger" | "neutral";

interface EstadoPuntoProps {
  color: EstadoColor;
  children: React.ReactNode;
}

/** Estado de tabla como punto con brillo + texto, sin píldora de color. */
export function EstadoPunto({ color, children }: EstadoPuntoProps) {
  return (
    <span className={[styles.estado, styles[color]].join(" ")}>
      <i className={styles.dot} aria-hidden="true" />
      {children}
    </span>
  );
}
