import { TEXTO_DERECHOS } from "../../lib/derechos";
import styles from "./PieDerechos.module.css";

/** Footer discreto con los derechos de autor. No se usa en el recibo ni en
 * lo impreso (esas rutas están fuera del layout y además se oculta al
 * imprimir). */
export function PieDerechos({ className }: { className?: string }) {
  return (
    <footer className={[styles.pie, className].filter(Boolean).join(" ")}>
      <p>{TEXTO_DERECHOS}</p>
    </footer>
  );
}
