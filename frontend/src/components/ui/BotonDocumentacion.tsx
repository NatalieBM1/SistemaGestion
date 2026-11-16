import { BookOpen } from "lucide-react";
import styles from "./BotonDocumentacion.module.css";

/** Botón "Documentación": abre la sección de la guía de usuario que
 * corresponde a la pantalla actual, en una pestaña nueva (para no perder lo
 * que el usuario está haciendo). En móvil se ve solo el ícono, con tooltip. */
export function BotonDocumentacion({ destino }: { destino: string }) {
  return (
    <a
      href={destino}
      target="_blank"
      rel="noopener"
      className={styles.boton}
      title="Abrir la guía de usuario de esta pantalla (pestaña nueva)"
      aria-label="Documentación: abrir la guía de usuario de esta pantalla en una pestaña nueva"
    >
      <BookOpen size={16} aria-hidden="true" />
      <span className={styles.texto}>Documentación</span>
    </a>
  );
}
