/** Quita los ceros a la izquierda del consecutivo para mostrar en
 * pantalla (ej. "GTS-006525" -> "GTS-6525"). Es solo presentación: lo
 * que se guarda en la base y se usa para buscar/filtrar no cambia.
 * Si el número no sigue el patrón PREFIJO-DIGITOS (ej. remisiones
 * manuales con texto libre), se devuelve tal cual, sin tocarlo. */
export function formatNumeroRemision(numero: string | null | undefined): string {
  if (!numero) return "";
  const match = numero.match(/^([A-Za-z]+)-0*(\d+)$/);
  if (!match) return numero;
  return `${match[1]}-${match[2]}`;
}
