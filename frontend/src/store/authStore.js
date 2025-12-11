import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../services/api'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      
      login: async (email, password) => {
        set({ isLoading: true })
        try {
          const response = await api.post('/api/v1/auth/login/', { email, password })
          const { access, refresh, user } = response.data
          
          // Set auth header
          api.defaults.headers.common['Authorization'] = `Bearer ${access}`
          
          set({
            token: access,
            refreshToken: refresh,
            user: user,
            isAuthenticated: true,
            isLoading: false,
          })
          
          return { success: true }
        } catch (error) {
          set({ isLoading: false })
          return { 
            success: false, 
            error: error.response?.data?.detail || 'Login xatosi' 
          }
        }
      },
      
      logout: () => {
        delete api.defaults.headers.common['Authorization']
        set({
          user: null,
          token: null,
          refreshToken: null,
          isAuthenticated: false,
        })
      },
      
      refreshAccessToken: async () => {
        const { refreshToken } = get()
        if (!refreshToken) return false
        
        try {
          const response = await api.post('/api/v1/auth/refresh/', {
            refresh: refreshToken,
          })
          const { access } = response.data
          
          api.defaults.headers.common['Authorization'] = `Bearer ${access}`
          set({ token: access })
          
          return true
        } catch {
          get().logout()
          return false
        }
      },
      
      updateProfile: async (data) => {
        try {
          const response = await api.patch('/api/v1/auth/profile/', data)
          set({ user: response.data })
          return { success: true }
        } catch (error) {
          return { 
            success: false, 
            error: error.response?.data || 'Profil yangilash xatosi' 
          }
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

// Initialize API with token on app load
const token = useAuthStore.getState().token
if (token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`
}
