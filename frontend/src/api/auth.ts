import { apiClient } from "./client";

export const authApi = {
  forgotPassword: (email: string) =>
    apiClient.post<{ detail: string }>("/api/auth/forgot-password", { email }),

  /** Cambia la propia contraseña (con sesión). Devuelve tokens nuevos: las
   * sesiones de otros equipos quedan cerradas y esta sigue abierta. */
  cambiarPassword: (password_actual: string, nueva_password: string) =>
    apiClient.post<{
      access_token: string;
      refresh_token: string;
      usuario: { id: number; nombre: string; email: string; roles: string[]; permisos?: string[] };
    }>("/api/auth/cambiar-password", { password_actual, nueva_password }),

  resetPassword: (email: string, codigo: string, nueva_password: string) =>
    apiClient.post<{ detail: string }>("/api/auth/reset-password", {
      email,
      codigo,
      nueva_password,
    }),
};
