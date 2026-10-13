export const ESTADO_FACTURACION_LABEL: Record<string, string> = {
  NO_FACTURADA: "No facturada",
  FACTURADA_PARCIAL: "Facturada parcial",
  FACTURADA: "Facturada",
};

export const ESTADO_FACTURACION_VARIANT: Record<string, "neutral" | "warning" | "success"> = {
  NO_FACTURADA: "neutral",
  FACTURADA_PARCIAL: "warning",
  FACTURADA: "success",
};
