import axios from 'axios'
import { authToken } from '../utils/authToken'
import { useAuthStore } from '../store/authSlice'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// Crear instancia de Axios
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor para añadir token en requests
apiClient.interceptors.request.use(
  (config) => {
    const token = authToken.get()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // Añadir session token si existe para carrito de invitado
    const sessionToken = localStorage.getItem('session_token')
    if (sessionToken && !token) {
      config.headers['X-Session-Token'] = sessionToken
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Interceptor para manejar respuestas y errores
apiClient.interceptors.response.use(
  (response) => {
    // Guardar session token si viene en headers
    const sessionToken = response.headers['x-session-token']
    if (sessionToken) {
      localStorage.setItem('session_token', sessionToken)
    }
    
    return response
  },
  (error) => {
    // Si recibimos 401, limpiar sesión y redirigir a login
    if (error.response?.status === 401) {
      const { logout } = useAuthStore.getState()
      authToken.remove()
      logout()
      
      // Solo redirigir si no estamos ya en login
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    
    // Mantener todos los errores visibles para debugging
    // Los errores son útiles para identificar problemas y arreglarlos más adelante
    return Promise.reject(error)
  }
)

export default apiClient





