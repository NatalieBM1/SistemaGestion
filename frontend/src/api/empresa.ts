import { apiClient } from "./client";

export interface Empresa {
  nombre: string;
  nit: string;
  direccion: string;
  telefono: string | null;
  email: string | null;
  ciudad: string | null;
  responsabilidad_iva: string;
  resolucion_habilitacion: string;
}

/** No hay tabla dedicada para los datos de la propia empresa: el backend la
 * resuelve reutilizando el Tercero que la representa (ver
 * backend/app/routers/empresa.py). */
export async function getEmpresa(): Promise<Empresa> {
  const { data } = await apiClient.get<Empresa>("/api/empresa");
  return data;
}
