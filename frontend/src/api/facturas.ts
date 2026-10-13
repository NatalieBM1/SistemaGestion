import { apiClient } from "./client";
import type { PaginatedResponse } from "./catalogos";

export interface Factura {
  numero_factura: string;
  fecha_factura: string;
  cantidad_remisiones: number;
  valor_total_facturado: string;
}

export interface RemisionFacturacion {
  id: number;
  remision_id: number;
  numero_remision: string | null;
  tipo_facturacion: "TOTAL" | "PARCIAL";
  valor_facturado: string;
  anulada: boolean;
  anulada_en: string | null;
  creado_en: string;
}

export interface RemisionFacturacionHistorial extends RemisionFacturacion {
  numero_factura: string;
  fecha_factura: string;
}

export interface ResumenFacturacionRemision {
  remision_id: number;
  valor_total: string;
  valor_facturado: string;
  saldo_pendiente: string;
  estado_facturacion: string;
}

export interface FacturarRemisionResponse {
  remision_facturacion_id: number;
  numero_factura: string;
  tipo_facturacion: string;
  valor_facturado: string;
  estado_facturacion: string;
  valor_facturado_total: string;
  saldo_pendiente: string;
}

export interface ActualizarFacturaResponse {
  numero_factura: string;
  fecha_factura: string;
  remisiones_afectadas: number;
  remisiones_ids: number[];
}

export interface CargaExcelResponse {
  filas_totales: number;
  filas_exitosas: number;
  filas_error: number;
  detalle_errores: Record<string, unknown>[];
}

export interface FacturaListParams {
  page: number;
  page_size?: number;
  desde?: string;
  hasta?: string;
  numero_factura?: string;
}

export async function listFacturas(params: FacturaListParams): Promise<PaginatedResponse<Factura>> {
  const { data } = await apiClient.get<PaginatedResponse<Factura>>("/api/facturas", {
    params: { page_size: 20, ...params },
  });
  return data;
}

export async function getRemisionesDeFactura(numeroFactura: string): Promise<RemisionFacturacion[]> {
  const { data } = await apiClient.get<RemisionFacturacion[]>(
    `/api/facturas/${encodeURIComponent(numeroFactura)}/remisiones`,
  );
  return data;
}

export async function actualizarFactura(payload: {
  numero_factura_actual: string;
  numero_factura_nuevo?: string;
  fecha_factura_nueva?: string;
}): Promise<ActualizarFacturaResponse> {
  const { data } = await apiClient.put<ActualizarFacturaResponse>("/api/facturas/actualizar", payload);
  return data;
}

export async function getResumenFacturacion(remisionId: number): Promise<ResumenFacturacionRemision> {
  const { data } = await apiClient.get<ResumenFacturacionRemision>(
    `/api/remisiones/${remisionId}/resumen-facturacion`,
  );
  return data;
}

export async function getHistorialFacturacion(remisionId: number): Promise<RemisionFacturacionHistorial[]> {
  const { data } = await apiClient.get<RemisionFacturacionHistorial[]>(
    `/api/remisiones/${remisionId}/facturaciones`,
  );
  return data;
}

export async function facturarRemision(
  remisionId: number,
  payload: { numero_factura: string; fecha_factura: string; tipo: "TOTAL" | "PARCIAL"; valor_facturado?: number },
): Promise<FacturarRemisionResponse> {
  const { data } = await apiClient.post<FacturarRemisionResponse>(
    `/api/remisiones/${remisionId}/facturar`,
    payload,
  );
  return data;
}

export async function anularFacturacion(remisionId: number, remisionFacturacionId: number): Promise<void> {
  await apiClient.delete(`/api/remisiones/${remisionId}/facturar/${remisionFacturacionId}`);
}

async function subirExcel(endpoint: string, file: File): Promise<CargaExcelResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await apiClient.post<CargaExcelResponse>(endpoint, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export const facturarMasivoExcel = (file: File) => subirExcel("/api/facturas/facturar-masivo", file);
export const eliminarPorExcel = (file: File) => subirExcel("/api/facturas/eliminar-por-excel", file);
export const actualizarPorExcel = (file: File) => subirExcel("/api/facturas/actualizar-por-excel", file);
