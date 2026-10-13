import axios from "axios";
import { apiClient } from "./client";

export interface ReporteFiltros {
  desde?: string;
  hasta?: string;
  cliente_id?: number;
  proyecto_id?: number;
  vehiculo_id?: number;
  camabaja_id?: number;
}

async function descargarReporte(endpoint: string, filtros: ReporteFiltros): Promise<Blob> {
  const { data } = await apiClient.get<Blob>(endpoint, {
    params: filtros,
    responseType: "blob",
  });
  return data;
}

export const descargarReporteGeneral = (filtros: ReporteFiltros) =>
  descargarReporte("/api/reportes/remisiones-general", filtros);

export const descargarReporteFacturadas = (filtros: ReporteFiltros) =>
  descargarReporte("/api/reportes/remisiones-facturadas", filtros);

/** Dispara la descarga de un Blob en el navegador con el nombre dado. */
export function guardarBlobComoArchivo(blob: Blob, nombreArchivo: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = nombreArchivo;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

/** apiClient.get con responseType "blob" devuelve el cuerpo de error (JSON de
 * FastAPI) como Blob en vez de objeto parseado — hay que leerlo aparte para
 * extraer el mensaje real (detail) en vez de mostrar un genérico. */
export async function getBlobErrorMessage(error: unknown, fallback: string): Promise<string> {
  if (axios.isAxiosError(error)) {
    if (!error.response) return "No se pudo conectar con el servidor.";
    const data = error.response.data;
    if (data instanceof Blob) {
      try {
        const text = await data.text();
        const parsed = JSON.parse(text);
        if (typeof parsed.detail === "string") return parsed.detail;
        if (Array.isArray(parsed.detail) && parsed.detail[0]?.msg) return parsed.detail[0].msg;
      } catch {
        // el cuerpo no era JSON; se usa el mensaje genérico
      }
    }
  }
  return fallback;
}
