import { apiClient } from "./client";
import type { PaginatedResponse } from "./catalogos";

export interface Tercero {
  id: number;
  identificacion: string;
  nombre: string;
  direccion: string | null;
  municipio_id: number | null;
  municipio_nombre: string | null;
  email: string | null;
  telefono: string | null;
  regimen: string | null;
  tiene_licencia: boolean | null;
  fecha_vencimiento_licencia: string | null;
  creado_en: string;
  tipos: string[];
}

export interface TerceroListParams {
  page: number;
  page_size?: number;
  q?: string;
  tipo?: string;
  ordenar_por?: string;
  sentido?: "asc" | "desc";
}

export async function listTerceros(params: TerceroListParams): Promise<PaginatedResponse<Tercero>> {
  const { data } = await apiClient.get<PaginatedResponse<Tercero>>("/api/terceros", {
    params: { page_size: 20, ...params },
  });
  return data;
}

export async function getTercero(id: number): Promise<Tercero> {
  const { data } = await apiClient.get<Tercero>(`/api/terceros/${id}`);
  return data;
}

export async function createTercero(payload: Record<string, unknown>): Promise<Tercero> {
  const { data } = await apiClient.post<Tercero>("/api/terceros", payload);
  return data;
}

export async function updateTercero(id: number, payload: Record<string, unknown>): Promise<Tercero> {
  const { data } = await apiClient.put<Tercero>(`/api/terceros/${id}`, payload);
  return data;
}

export async function asociarTipoATercero(id: number, tipoId: number): Promise<Tercero> {
  const { data } = await apiClient.post<Tercero>(`/api/terceros/${id}/tipos`, { tipo_id: tipoId });
  return data;
}

export async function desasociarTipoDeTercero(id: number, tipoId: number): Promise<void> {
  await apiClient.delete(`/api/terceros/${id}/tipos/${tipoId}`);
}

export interface TipoTercero {
  id: number;
  nombre: string;
}

export async function listTiposTercero(): Promise<TipoTercero[]> {
  const { data } = await apiClient.get("/api/catalogos/tipos_tercero", { params: { page_size: 50 } });
  return data.items as TipoTercero[];
}
