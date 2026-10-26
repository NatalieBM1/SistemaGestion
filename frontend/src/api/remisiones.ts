import { apiClient } from "./client";
import type { PaginatedResponse } from "./catalogos";

export interface Remision {
  id: number;
  numero_remision: string;
  prefijo_id: number;
  consecutivo: string;
  orden_servicio_id: number | null;
  fecha: string;
  forma_pago_id: number | null;
  cliente_id: number;
  cliente_nombre: string | null;
  conductor_id: number | null;
  conductor_nombre: string | null;
  origen_municipio_id: number;
  origen_municipio_nombre: string | null;
  destino_municipio_id: number;
  destino_municipio_nombre: string | null;
  proyecto_id: number | null;
  tramo_id: number | null;
  tipo_servicio_id: number | null;
  vehiculo_id: number | null;
  vehiculo_placa: string | null;
  camabaja_id: number | null;
  kilometros: string | null;
  hora_salida: string | null;
  hora_llegada: string | null;
  remision_agresur: string | null;
  observaciones: string | null;
  usuario_creador_id: number;
  estado_facturacion: "NO_FACTURADA" | "FACTURADA_PARCIAL" | "FACTURADA";
  valor_total: string;
  creado_en: string;
  actualizado_en: string;
}

export interface RemisionProducto {
  id: number;
  remision_id: number;
  producto_id: number;
  producto_nombre: string | null;
  cantidad: string;
  unidad_medida_id: number | null;
  unidad_medida_nombre: string | null;
  valor_material: string;
  valor_flete: string;
  valor_camabaja: string;
  numero_viajes: number;
  valor_comision: string;
  valor_costo: string;
}

export interface RemisionDetalle extends Remision {
  productos: RemisionProducto[];
}

export interface RemisionListParams {
  page: number;
  page_size?: number;
  desde?: string;
  hasta?: string;
  numero_remision?: string;
  estado_facturacion?: string;
  q?: string;
  factura?: string;
  placa?: string;
  proyecto_id?: number;
  tercero_id?: number;
  ordenar_por?: string;
  sentido?: "asc" | "desc";
}

export async function listRemisiones(
  params: RemisionListParams,
): Promise<PaginatedResponse<Remision>> {
  const { data } = await apiClient.get<PaginatedResponse<Remision>>("/api/remisiones", {
    params: { page_size: 20, ...params },
  });
  return data;
}

export async function getRemision(id: number): Promise<RemisionDetalle> {
  const { data } = await apiClient.get<RemisionDetalle>(`/api/remisiones/${id}`);
  return data;
}

export async function createRemision(payload: Record<string, unknown>): Promise<Remision> {
  const { data } = await apiClient.post<Remision>("/api/remisiones", payload);
  return data;
}

export async function updateRemision(
  id: number,
  payload: Record<string, unknown>,
): Promise<{ remision: Remision; advertencia: string | null }> {
  const { data } = await apiClient.put(`/api/remisiones/${id}`, payload);
  return data;
}

export async function crearProductoRemision(
  remisionId: number,
  payload: Record<string, unknown>,
): Promise<{ producto: RemisionProducto; alerta_saldo_bajo: string | null }> {
  const { data } = await apiClient.post(`/api/remisiones/${remisionId}/productos`, payload);
  return data;
}

export async function actualizarProductoRemision(
  remisionId: number,
  productoId: number,
  payload: Record<string, unknown>,
): Promise<{ producto: RemisionProducto; alerta_saldo_bajo: string | null }> {
  const { data } = await apiClient.put(
    `/api/remisiones/${remisionId}/productos/${productoId}`,
    payload,
  );
  return data;
}

export async function eliminarProductoRemision(
  remisionId: number,
  productoId: number,
): Promise<void> {
  await apiClient.delete(`/api/remisiones/${remisionId}/productos/${productoId}`);
}

export async function copiarRemision(
  remisionId: number,
  copiarProductos: boolean,
  numeroRemision?: string,
): Promise<{ remision: RemisionDetalle; alerta_saldo_bajo: string | null }> {
  const { data } = await apiClient.post(`/api/remisiones/${remisionId}/copiar`, {
    copiar_productos: copiarProductos,
    numero_remision: numeroRemision || undefined,
  });
  return data;
}
