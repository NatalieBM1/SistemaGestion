export function formatMoney(value: string | number): string {
  const n = typeof value === "string" ? Number(value) : value;
  return n.toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
}
