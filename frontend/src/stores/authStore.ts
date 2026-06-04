/**
 * Global authentication store using Zustand.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import { User } from "@/types";
import { authApi, setTokens, clearTokens, getAccessToken } from "@/services/api";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, full_name: string) => Promise<void>;
  logout: () => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: !!getAccessToken(),
      isLoading: false,
      error: null,

      login: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
          const { data } = await authApi.login(email, password);
          setTokens(data.access_token, data.refresh_token);
          set({
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (err: unknown) {
          const error = err as { response?: { data?: { detail?: string } } };
          set({
            isLoading: false,
            error: error.response?.data?.detail || "Login failed",
            isAuthenticated: false,
          });
          throw err;
        }
      },

      register: async (email, password, full_name) => {
        set({ isLoading: true, error: null });
        try {
          await authApi.register({ email, password, full_name });
          set({ isLoading: false });
        } catch (err: unknown) {
          const error = err as { response?: { data?: { detail?: string } } };
          set({
            isLoading: false,
            error: error.response?.data?.detail || "Registration failed",
          });
          throw err;
        }
      },

      logout: () => {
        clearTokens();
        set({ user: null, isAuthenticated: false });
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: "finsight-auth",
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);
