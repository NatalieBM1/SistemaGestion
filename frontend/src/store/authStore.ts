import { create } from "zustand";
import { apiClient } from "../api/client";

export interface AuthUser {
  id: number;
  nombre: string;
  email: string;
  roles: string[];
  permisos: string[];
}

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  setTokens: (accessToken: string, refreshToken: string) => void;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loadUserFromMe: () => Promise<void>;
}

const STORAGE_KEY = "sgt.auth";

interface StoredAuth {
  accessToken: string;
  refreshToken: string;
}

function readStoredAuth(): StoredAuth | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as StoredAuth) : null;
  } catch {
    return null;
  }
}

function writeStoredAuth(data: StoredAuth | null): void {
  try {
    if (data) localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    // localStorage puede no estar disponible (modo privado, cuota, etc.)
  }
}

const stored = readStoredAuth();

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: stored?.accessToken ?? null,
  refreshToken: stored?.refreshToken ?? null,
  isAuthenticated: Boolean(stored?.accessToken),
  isInitializing: true,

  setTokens: (accessToken, refreshToken) => {
    writeStoredAuth({ accessToken, refreshToken });
    set({ accessToken, refreshToken, isAuthenticated: true });
  },

  login: async (email, password) => {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    const { data } = await apiClient.post("/api/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    get().setTokens(data.access_token, data.refresh_token);
    set({
      user: {
        id: data.usuario.id,
        nombre: data.usuario.nombre,
        email: data.usuario.email,
        roles: data.usuario.roles,
        permisos: data.usuario.permisos ?? [],
      },
    });
  },

  logout: () => {
    writeStoredAuth(null);
    set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false });
  },

  loadUserFromMe: async () => {
    if (!get().accessToken) {
      set({ isInitializing: false });
      return;
    }
    try {
      const { data } = await apiClient.get("/api/auth/me");
      set({ user: data, isAuthenticated: true, isInitializing: false });
    } catch {
      get().logout();
      set({ isInitializing: false });
    }
  },
}));
