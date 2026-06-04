/**
 * Axios API client with JWT auth interceptor and automatic token refresh.
 */
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const API_PREFIX = "/api/v1";

// ── Token storage ────────────────────────────────────────────────────────────
export const getAccessToken = () => localStorage.getItem("access_token");
export const getRefreshToken = () => localStorage.getItem("refresh_token");
export const setTokens = (access: string, refresh: string) => {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
};
export const clearTokens = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
};

// ── Axios instance ────────────────────────────────────────────────────────────
const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}${API_PREFIX}`,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// Request interceptor: attach bearer token
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: handle 401 → refresh token
let isRefreshing = false;
let refreshQueue: Array<(token: string) => void> = [];

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        clearTokens();
        window.location.href = "/login";
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve) => {
          refreshQueue.push((token: string) => {
            originalRequest.headers!.Authorization = `Bearer ${token}`;
            resolve(api(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { data } = await axios.post(`${API_URL}${API_PREFIX}/auth/refresh`, {
          refresh_token: refreshToken,
        });
        setTokens(data.access_token, data.refresh_token);
        refreshQueue.forEach((cb) => cb(data.access_token));
        refreshQueue = [];
        originalRequest.headers!.Authorization = `Bearer ${data.access_token}`;
        return api(originalRequest);
      } catch {
        clearTokens();
        window.location.href = "/login";
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// ── Auth API ──────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data: { email: string; password: string; full_name: string }) =>
    api.post("/auth/register", data),
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  refresh: (refresh_token: string) =>
    api.post("/auth/refresh", { refresh_token }),
};

// ── Transactions API ──────────────────────────────────────────────────────────
export const transactionsApi = {
  list: (params?: Record<string, unknown>) =>
    api.get("/transactions", { params }),
  create: (data: Record<string, unknown>) =>
    api.post("/transactions", data),
  update: (id: string, data: Record<string, unknown>) =>
    api.patch(`/transactions/${id}`, data),
  summaryByCategory: (params?: { start_date?: string; end_date?: string }) =>
    api.get("/transactions/summary/by-category", { params }),
};

// ── Budget API ────────────────────────────────────────────────────────────────
export const budgetsApi = {
  list: () => api.get("/budgets"),
  create: (data: Record<string, unknown>) => api.post("/budgets", data),
  delete: (id: string) => api.delete(`/budgets/${id}`),
};

// ── Insights & Analytics API ──────────────────────────────────────────────────
export const insightsApi = {
  getInsights: () => api.get("/insights"),
  getHealthScore: () => api.get("/health-score"),
  getForecast: (horizon_days: number = 30) =>
    api.get("/forecast", { params: { horizon_days } }),
  getAnomalies: () => api.get("/anomalies"),
};
