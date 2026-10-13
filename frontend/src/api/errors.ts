import axios from "axios";

/** Extrae el mensaje de error real del backend ({"detail": "..."}) de un
 * error de axios, con un mensaje genérico como respaldo. FastAPI también
 * puede devolver `detail` como una lista de errores de validación (422). */
export function getApiErrorMessage(error: unknown, fallback = "Ocurrió un error inesperado."): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      const first = detail[0];
      if (first && typeof first.msg === "string") return first.msg;
    }
    if (!error.response) return "No se pudo conectar con el servidor.";
  }
  return fallback;
}
