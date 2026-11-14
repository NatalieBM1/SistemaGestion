/** True si el usuario dejó texto seleccionado dentro de `elemento` (o en
 * cualquier parte si no se pasa). Sirve para no navegar con un clic que en
 * realidad era el final de una selección de texto. */
export function haySeleccionDeTexto(elemento?: Element | null): boolean {
  const seleccion = window.getSelection();
  if (!seleccion || seleccion.isCollapsed || !seleccion.toString().trim()) return false;
  return !elemento || (seleccion.anchorNode != null && elemento.contains(seleccion.anchorNode));
}

/** Copia texto al portapapeles. Usa `navigator.clipboard` cuando existe
 * (requiere https o localhost); si no está disponible o falla, cae a la
 * forma clásica con un <textarea> temporal y `document.execCommand`.
 * Devuelve si se pudo copiar. */
export async function copiarAlPortapapeles(texto: string): Promise<boolean> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(texto);
      return true;
    }
  } catch {
    // sin permiso o contexto inseguro: se intenta la alternativa
  }
  try {
    const area = document.createElement("textarea");
    area.value = texto;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(area);
    return ok;
  } catch {
    return false;
  }
}
