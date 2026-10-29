import { apiClient } from "./client";
import type { PaginatedResponse } from "./catalogos";
import type { Ordenamiento } from "../hooks/useOrdenamiento";

function paramsOrden(orden?: Ordenamiento) {
  return orden?.campo && orden.sentido ? { ordenar_por: orden.campo, sentido: orden.sentido } : {};
}

export interface Departamento {
  id: number;
  codigo_dane: string;
  nombre: string;
}

export interface Municipio {
  id: number;
  codigo_dane: string;
  nombre: string;
  departamento_id: number;
}

export async function listDepartamentos(
  page: number,
  q: string,
  pageSize = 50,
  orden?: Ordenamiento,
): Promise<PaginatedResponse<Departamento>> {
  const { data } = await apiClient.get<PaginatedResponse<Departamento>>("/api/ubicaciones/departamentos", {
    params: { page, page_size: pageSize, q: q || undefined, ...paramsOrden(orden) },
  });
  return data;
}

export async function createDepartamento(payload: Record<string, unknown>): Promise<Departamento> {
  const { data } = await apiClient.post<Departamento>("/api/ubicaciones/departamentos", payload);
  return data;
}

export async function updateDepartamento(id: number, payload: Record<string, unknown>): Promise<Departamento> {
  const { data } = await apiClient.put<Departamento>(`/api/ubicaciones/departamentos/${id}`, payload);
  return data;
}

export async function listMunicipiosDeDepartamento(
  departamentoId: number,
  page: number,
  q: string,
  pageSize = 50,
  orden?: Ordenamiento,
): Promise<PaginatedResponse<Municipio>> {
  const { data } = await apiClient.get<PaginatedResponse<Municipio>>(
    `/api/ubicaciones/departamentos/${departamentoId}/municipios`,
    { params: { page, page_size: pageSize, q: q || undefined, ...paramsOrden(orden) } },
  );
  return data;
}

export async function createMunicipio(payload: Record<string, unknown>): Promise<Municipio> {
  const { data } = await apiClient.post<Municipio>("/api/ubicaciones/municipios", payload);
  return data;
}

export async function updateMunicipio(id: number, payload: Record<string, unknown>): Promise<Municipio> {
  const { data } = await apiClient.put<Municipio>(`/api/ubicaciones/municipios/${id}`, payload);
  return data;
}
