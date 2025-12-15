import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://192.168.200.232:3000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Get token from localStorage
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    // If 401 and we haven't tried to refresh yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      // Try to refresh the token
      const authStore = (await import('../store/authStore')).useAuthStore.getState()
      const refreshed = await authStore.refreshAccessToken()
      
      if (refreshed) {
        const newToken = authStore.token
        originalRequest.headers['Authorization'] = `Bearer ${newToken}`
        return api(originalRequest)
      }
    }
    
    return Promise.reject(error)
  }
)

export default api
