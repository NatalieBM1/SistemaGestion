import { apiClient } from "./client";
import type { PaginatedResponse } from "./catalogos";

export interface Activo {
  id: number;
  placa: string;
  tipo_activo: string;
  clase: string;
  empresa_id: number;
  empresa_nombre: string | null;
  es_segunda_mano: boolean;
  bloqueado: boolean;
  creado_en: string;
}

export interface ActivoListParams {
  page: number;
  page_size?: number;
  q?: string;
}

export async function listActivos(params: ActivoListParams): Promise<PaginatedResponse<Activo>> {
  const { data } = await apiClient.get<PaginatedResponse<Activo>>("/api/activos", {
    params: { page_size: 20, ...params },
  });
  return data;
}

export async function createActivo(payload: Record<string, unknown>): Promise<Activo> {
  const { data } = await apiClient.post<Activo>("/api/activos", payload);
  return data;
}

export async function updateActivo(id: number, payload: Record<string, unknown>): Promise<Activo> {
  const { data } = await apiClient.put<Activo>(`/api/activos/${id}`, payload);
  return data;
}

export async function alternarBloqueoActivo(id: number): Promise<Activo> {
  const { data } = await apiClient.patch<Activo>(`/api/activos/${id}/bloquear`);
  return data;
}
