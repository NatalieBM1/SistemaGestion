import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "../store/authStore";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

/** Cliente autenticado: agrega el Bearer token y maneja el refresh en 401. */
export const apiClient = axios.create({ baseURL: API_URL });

/** Cliente "crudo", sin interceptores — usado solo para /api/auth/refresh,
 * para no disparar el propio interceptor de 401 al refrescar. */
const rawClient = axios.create({ baseURL: API_URL });

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refreshToken = useAuthStore.getState().refreshToken;
  if (!refreshToken) {
    throw new Error("No hay refresh_token disponible.");
  }
  const { data } = await rawClient.post("/api/auth/refresh", { refresh_token: refreshToken });
  useAuthStore.getState().setTokens(data.access_token, refreshToken);
  return data.access_token as string;
}

type RetryableRequestConfig = InternalAxiosRequestConfig & { _retry?: boolean };

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequestConfig | undefined;
    const url = originalRequest?.url ?? "";
    const isAuthEndpoint = url.includes("/api/auth/login") || url.includes("/api/auth/refresh");
    const hadToken = Boolean(useAuthStore.getState().accessToken);

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !isAuthEndpoint &&
      hadToken
    ) {
      originalRequest._retry = true;
      try {
        if (!refreshPromise) {
          refreshPromise = refreshAccessToken().finally(() => {
            refreshPromise = null;
          });
        }
        const newToken = await refreshPromise;
        originalRequest.headers.set("Authorization", `Bearer ${newToken}`);
        return apiClient(originalRequest);
      } catch {
        useAuthStore.getState().logout();
        window.location.href = "/login";
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  },
);
