import { apiClient } from "./client";

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export type CatalogoItem = Record<string, unknown> & { id: number };

export async function listCatalogo(
  endpoint: string,
  page: number,
  q: string,
  pageSize = 20,
  ordenarPor?: string,
  sentido?: "asc" | "desc",
): Promise<PaginatedResponse<CatalogoItem>> {
  const { data } = await apiClient.get<PaginatedResponse<CatalogoItem>>(endpoint, {
    params: {
      page,
      page_size: pageSize,
      q: q || undefined,
      ordenar_por: ordenarPor,
      sentido,
    },
  });
  return data;
}

export async function createCatalogoItem(
  endpoint: string,
  payload: Record<string, unknown>,
): Promise<CatalogoItem> {
  const { data } = await apiClient.post<CatalogoItem>(endpoint, payload);
  return data;
}

export async function updateCatalogoItem(
  endpoint: string,
  id: number,
  payload: Record<string, unknown>,
): Promise<CatalogoItem> {
  const { data } = await apiClient.put<CatalogoItem>(`${endpoint}/${id}`, payload);
  return data;
}

export async function deleteCatalogoItem(endpoint: string, id: number): Promise<void> {
  await apiClient.delete(`${endpoint}/${id}`);
}
