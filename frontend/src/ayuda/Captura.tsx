import { ImageOff, X } from "lucide-react";
import { useEffect, useState } from "react";
import styles from "./Guia.module.css";

/** Capturas de pantalla de la guía: imagenes/<seccion>/<nn>-<descripcion>.png.
 * Si el archivo no existe todavía, se muestra un recuadro "Captura
 * pendiente" (no rompe el build); si existe, la imagen con carga diferida y
 * clic para ampliar. */
const IMAGENES = import.meta.glob("./imagenes/**/*.png", {
  eager: true,
  query: "?url",
  import: "default",
}) as Record<string, string>;

/** La carpeta y el archivo se comparan sin mayúsculas, tildes, guiones ni
 * espacios: "PrimerosPasos/01-Iniciar-Sesion.png" sirve para la sección
 * "primeros-pasos" y la captura "01-iniciar-sesion.png". */
export function normalizarRutaImagen(ruta: string): string {
  return ruta
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .split("/")
    .map((parte) => parte.replace(/[^a-z0-9.]/g, ""))
    .join("/");
}

const POR_CLAVE = new Map(
  Object.entries(IMAGENES).map(([ruta, url]) => [normalizarRutaImagen(ruta.replace("./imagenes/", "")), url]),
);

export function rutaImagen(seccion: string, archivo: string): string | undefined {
  return POR_CLAVE.get(normalizarRutaImagen(`${seccion}/${archivo}`));
}

export function Captura({ seccion, archivo, descripcion }: { seccion: string; archivo: string; descripcion: string }) {
  const src = rutaImagen(seccion, archivo);
  const [ampliada, setAmpliada] = useState(false);

  useEffect(() => {
    if (!ampliada) return;
    const cerrar = (e: KeyboardEvent) => e.key === "Escape" && setAmpliada(false);
    window.addEventListener("keydown", cerrar);
    return () => window.removeEventListener("keydown", cerrar);
  }, [ampliada]);

  if (!src) {
    return (
      <figure className={styles.capturaPendiente} role="img" aria-label={`Captura pendiente: ${descripcion}`}>
        <ImageOff size={22} aria-hidden="true" />
        <figcaption>
          <strong>Captura pendiente:</strong> <code>{archivo}</code> · {descripcion}
        </figcaption>
      </figure>
    );
  }
  return (
    <figure className={styles.captura}>
      <button type="button" className={styles.capturaBoton} onClick={() => setAmpliada(true)} aria-label={`Ampliar: ${descripcion}`}>
        <img src={src} alt={descripcion} loading="lazy" />
      </button>
      <figcaption>{descripcion}</figcaption>
      {ampliada && (
        <div className={styles.lightbox} role="dialog" aria-modal="true" aria-label={descripcion} onClick={() => setAmpliada(false)}>
          <button type="button" className={styles.lightboxCerrar} aria-label="Cerrar imagen" onClick={() => setAmpliada(false)}>
            <X size={20} />
          </button>
          <img src={src} alt={descripcion} />
        </div>
      )}
    </figure>
  );
}
