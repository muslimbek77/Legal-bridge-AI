import axios from "axios";

export const API_BASE_URL =
  (import.meta.env.VITE_API_URL || "http://192.168.200.232:3000").replace(/\/+$/, "");

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor
api.interceptors.request.use(
  async (config) => {
    // The auth state is persisted by Zustand under "auth-storage"; there is
    // no standalone localStorage entry named "token".
    const { useAuthStore } = await import("../store/authStore");
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    } else if (config.headers?.Authorization) {
      delete config.headers.Authorization;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const requestUrl = originalRequest?.url || "";
    const isAuthEndpoint = /\/auth\/(login|refresh)\//.test(requestUrl);

    // Never try to refresh a failed login or refresh request. The refresh
    // request itself bypasses this client, so expired refresh tokens cannot
    // create a recursive chain of requests.
    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !isAuthEndpoint
    ) {
      originalRequest._retry = true;

      const { useAuthStore } = await import("../store/authStore");
      const refreshed = await useAuthStore.getState().refreshAccessToken();

      if (refreshed) {
        const newToken = useAuthStore.getState().token;
        originalRequest.headers = originalRequest.headers || {};
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
