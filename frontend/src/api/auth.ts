import { apiClient } from "./client";

export const authApi = {
  forgotPassword: (email: string) =>
    apiClient.post<{ detail: string }>("/api/auth/forgot-password", { email }),

  resetPassword: (email: string, codigo: string, nueva_password: string) =>
    apiClient.post<{ detail: string }>("/api/auth/reset-password", {
      email,
      codigo,
      nueva_password,
    }),
};
