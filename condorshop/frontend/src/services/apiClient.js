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
    
    // Añadir session token para carrito de invitado (si no hay token de autenticación)
    // Si no existe, el backend lo generará automáticamente
    if (!token) {
      const sessionToken = localStorage.getItem('session_token')
      if (sessionToken) {
        config.headers['X-Session-Token'] = sessionToken
      }
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
    // Guardar session token si viene en headers (case-insensitive)
    const sessionToken = response.headers['x-session-token'] || 
                        response.headers['X-Session-Token'] ||
                        response.headers.get?.('x-session-token') ||
                        response.headers.get?.('X-Session-Token')
    if (sessionToken) {
      localStorage.setItem('session_token', sessionToken)
    }
    
    return response
  },
  (error) => {
    // Si recibimos 401, limpiar sesión
    if (error.response?.status === 401) {
      const { logout } = useAuthStore.getState()
      authToken.remove()
      logout()
      
      // Rutas públicas que NO deben redirigir a login (permiten checkout de invitados)
      const publicRoutes = [
        '/',
        '/cart',
        '/checkout/customer',
        '/checkout/address',
        '/checkout/payment',
        '/checkout/review',
        '/login',
        '/register',
        '/forgot-password',
        '/reset-password',
      ]
      
      // Rutas de productos y categorías (públicas)
      const isPublicRoute = publicRoutes.some(route => 
        window.location.pathname === route || 
        window.location.pathname.startsWith('/product/') ||
        window.location.pathname.startsWith('/category/')
      )
      
      // Solo redirigir a login si:
      // 1. No estamos ya en login
      // 2. NO estamos en una ruta pública (para permitir checkout de invitados)
      // 3. NO estamos en una ruta de checkout o carrito
      if (window.location.pathname !== '/login' && !isPublicRoute) {
        window.location.href = '/login'
      }
    }
    
    // Mantener todos los errores visibles para debugging
    // Los errores son útiles para identificar problemas y entender el proyecto
    return Promise.reject(error)
  }
)

export default apiClient





