import { apiClient } from "./client";

export const authApi = {
  forgotPassword: (email: string) =>
    apiClient.post<{ detail: string }>("/api/auth/forgot-password", { email }),

  verifyResetCode: (email: string, codigo: string) =>
    apiClient.post<{ detail: string }>("/api/auth/verify-reset-code", { email, codigo }),

  resetPassword: (email: string, codigo: string, nueva_password: string) =>
    apiClient.post<{ detail: string }>("/api/auth/reset-password", {
      email,
      codigo,
      nueva_password,
    }),
};
