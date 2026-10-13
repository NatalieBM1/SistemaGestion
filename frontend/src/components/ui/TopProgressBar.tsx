import { useIsFetching, useIsMutating } from "@tanstack/react-query";
import styles from "./TopProgressBar.module.css";

/** Único elemento "vivo" de la interfaz: visible solo mientras hay una
 * petición de red en curso (query o mutation de TanStack Query). */
export function TopProgressBar() {
  const isFetching = useIsFetching();
  const isMutating = useIsMutating();
  const active = isFetching > 0 || isMutating > 0;

  if (!active) return null;

  return <div className={styles.bar} aria-hidden="true" />;
}
