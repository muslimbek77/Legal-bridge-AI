import { create } from "zustand";
import { persist } from "zustand/middleware";
import axios from "axios";
import api, { API_BASE_URL } from "../services/api";

let refreshPromise = null;

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      // userDetails: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      isHydrated: false,

      login: async (email, password) => {
        set({ isLoading: true });
        try {
          const response = await api.post("/api/v1/auth/login/", {
            email,
            password,
          });
          const { access, refresh, user } = response.data;

          // Set auth header
          api.defaults.headers.common["Authorization"] = `Bearer ${access}`;

          set({
            token: access,
            refreshToken: refresh,
            user: user,
            isAuthenticated: true,
            isLoading: false,
          });

          return { success: true };
        } catch (error) {
          set({ isLoading: false });
          return {
            success: false,
            error: error.response?.data?.detail || "Login xatosi",
          };
        }
      },

      logout: () => {
        delete api.defaults.headers.common["Authorization"];
        set({
          user: null,
          token: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },

      refreshAccessToken: async () => {
        if (refreshPromise) return refreshPromise;

        const { refreshToken } = get();
        if (!refreshToken) {
          get().logout();
          return false;
        }

        refreshPromise = (async () => {
          try {
            // Use bare axios so an expired refresh token cannot re-enter the
            // API response interceptor and start another refresh attempt.
            const response = await axios.post(
              `${API_BASE_URL}/api/v1/auth/refresh/`,
              { refresh: refreshToken },
              { timeout: 10000 }
            );
            const { access, refresh: rotatedRefresh } = response.data;

            if (!access) throw new Error("Refresh response did not include an access token");
            // Do not restore a session if the user logged out or signed in
            // with different credentials while this request was in flight.
            if (get().refreshToken !== refreshToken) return false;

            api.defaults.headers.common["Authorization"] = `Bearer ${access}`;
            set({
              token: access,
              // Simple JWT may rotate refresh tokens. Persist the new token
              // when returned while keeping compatibility with non-rotating setups.
              ...(rotatedRefresh ? { refreshToken: rotatedRefresh } : {}),
              isAuthenticated: true,
            });

            return true;
          } catch (error) {
            // Invalid/expired refresh credentials require a fresh login.
            // Keep the session on transient server/network failures.
            if (
              [400, 401, 403].includes(error.response?.status) &&
              get().refreshToken === refreshToken
            ) {
              get().logout();
            }
            return false;
          } finally {
            refreshPromise = null;
          }
        })();

        return refreshPromise;
      },

      // fetchUserDetails: async (id) => {
      //   try {
      //     const token = get().token;
      //     const response = await api.get(`/api/v1/auth/users/${id}/`, {
      //       headers: {
      //         Authorization: `Bearer ${token}`,
      //       },
      //     });
      //     set({ userDetails: response.data });
      //     return { success: true };
      //   } catch (error) {
      //     return {
      //       success: false,
      //       error: error.response?.data || "Foydalanuvchi ma'lumotini olishda xato",
      //     };
      //   }
      // },

      updateProfile: async (data) => {
        try {
          const response = await api.patch("/api/v1/auth/profile/", data);

          // After patch, fetch the REAL latest user
          const userId = get().user?.id;

          if (!userId) throw new Error("User ID not found");

          const refreshedUser = await api.get(`/api/v1/auth/users/${userId}/`);

          set({ user: refreshedUser.data });

          return { success: true };
        } catch (error) {
          return {
            success: false,
            error: error.response?.data || "Profil yangilash xatosi",
          };
        }
      },
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        user: state.user,
        // userDetails: state.userDetails,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        state.isHydrated = true;
      },
    }
  )
);

// Initialize API with token on app load
const token = useAuthStore.getState().token;
if (token) {
  api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
}
