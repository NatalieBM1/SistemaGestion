export const ESTADO_FACTURACION_LABEL: Record<string, string> = {
  NO_FACTURADA: "No facturada",
  FACTURADA_PARCIAL: "Facturada parcial",
  FACTURADA: "Facturada",
  NO_APLICA: "No aplica facturación",
};

export const ESTADO_FACTURACION_VARIANT: Record<string, "neutral" | "warning" | "success"> = {
  NO_FACTURADA: "neutral",
  FACTURADA_PARCIAL: "warning",
  FACTURADA: "success",
  NO_APLICA: "neutral",
};

/** Opciones de los filtros de estado, en el orden en que se muestran. */
export const ESTADOS_FACTURACION = ["NO_FACTURADA", "FACTURADA_PARCIAL", "FACTURADA", "NO_APLICA"] as const;

/** Se puede facturar (o agregar a una factura): no está facturada del todo
 * ni marcada como «No aplica facturación». */
export function esFacturable(estado: string | null | undefined): boolean {
  return estado !== "FACTURADA" && estado !== "NO_APLICA";
}
