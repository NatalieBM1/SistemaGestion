import { apiClient } from "./client";
import type { PaginatedResponse } from "./catalogos";

export interface UsuarioAdmin {
  id: number;
  nombre: string;
  email: string;
  identificacion: string | null;
  activo: boolean;
  creado_en: string;
  actualizado_en: string;
  roles: string[];
}

export interface RolAdmin {
  id: number;
  nombre: string;
  permisos: string[];
}

export interface PermisoAdmin {
  id: number;
  codigo: string;
  modulo: string;
}

export async function listUsuarios(
  page: number,
  q: string,
  pageSize = 20,
  ordenarPor?: string,
  sentido?: "asc" | "desc",
): Promise<PaginatedResponse<UsuarioAdmin>> {
  const { data } = await apiClient.get<PaginatedResponse<UsuarioAdmin>>("/api/admin/usuarios", {
    params: { page, page_size: pageSize, q: q || undefined, ordenar_por: ordenarPor, sentido },
  });
  return data;
}

export async function createUsuario(payload: Record<string, unknown>): Promise<UsuarioAdmin> {
  const { data } = await apiClient.post<UsuarioAdmin>("/api/admin/usuarios", payload);
  return data;
}

export async function updateUsuario(id: number, payload: Record<string, unknown>): Promise<UsuarioAdmin> {
  const { data } = await apiClient.put<UsuarioAdmin>(`/api/admin/usuarios/${id}`, payload);
  return data;
}

export async function asignarRolAUsuario(usuarioId: number, rolId: number): Promise<UsuarioAdmin> {
  const { data } = await apiClient.post<UsuarioAdmin>(`/api/admin/usuarios/${usuarioId}/roles`, {
    roles_ids: [rolId],
  });
  return data;
}

export async function quitarRolDeUsuario(usuarioId: number, rolId: number): Promise<void> {
  await apiClient.delete(`/api/admin/usuarios/${usuarioId}/roles/${rolId}`);
}

export async function listRoles(page: number, q: string): Promise<PaginatedResponse<RolAdmin>> {
  const { data } = await apiClient.get<PaginatedResponse<RolAdmin>>("/api/admin/roles", {
    params: { page, page_size: 50, q: q || undefined },
  });
  return data;
}

export async function getRol(id: number): Promise<RolAdmin> {
  const { data } = await apiClient.get<RolAdmin>(`/api/admin/roles/${id}`);
  return data;
}

export async function asignarPermisoARol(rolId: number, permisoId: number): Promise<RolAdmin> {
  const { data } = await apiClient.post<RolAdmin>(`/api/admin/roles/${rolId}/permisos`, {
    permisos_ids: [permisoId],
  });
  return data;
}

export async function quitarPermisoDeRol(rolId: number, permisoId: number): Promise<void> {
  await apiClient.delete(`/api/admin/roles/${rolId}/permisos/${permisoId}`);
}

export async function listTodosLosPermisos(): Promise<PermisoAdmin[]> {
  const { data } = await apiClient.get<PaginatedResponse<PermisoAdmin>>("/api/admin/permisos", {
    params: { page_size: 100 },
  });
  return data.items;
}

export async function listTodosLosRoles(): Promise<RolAdmin[]> {
  const { data } = await apiClient.get<PaginatedResponse<RolAdmin>>("/api/admin/roles", {
    params: { page_size: 50 },
  });
  return data.items;
}

export async function listTodosLosUsuarios(): Promise<UsuarioAdmin[]> {
  const { data } = await apiClient.get<PaginatedResponse<UsuarioAdmin>>("/api/admin/usuarios", {
    params: { page_size: 100 },
  });
  return data.items;
}
