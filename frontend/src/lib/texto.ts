/** Para comparar textos de catálogo sin distinguir mayúsculas ni tildes
 * ("Cama baja" = "CAMA BAJA", "Metro cúbico" = "METRO CUBICO"). */
export function normalizarTexto(texto: string | null | undefined): string {
  return (texto ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toLowerCase();
}
