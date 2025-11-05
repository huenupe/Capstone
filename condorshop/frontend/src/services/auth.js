import apiClient from './apiClient'
import { authToken } from '../utils/authToken'

export const authService = {
  /**
   * Registro de nuevo usuario
   * @param {Object} data - { email, password, first_name, last_name }
   */
  register: async (data) => {
    const response = await apiClient.post('/auth/register', data)
    const { tokens, user } = response.data
    
    // Guardar token
    authToken.set(tokens.access)
    
    return { user, token: tokens.access }
  },

  /**
   * Login de usuario
   * @param {Object} credentials - { email, password }
   */
  login: async (credentials) => {
    const response = await apiClient.post('/auth/login', credentials)
    const { tokens, user } = response.data
    
    // Guardar token
    authToken.set(tokens.access)
    
    return { user, token: tokens.access }
  },

  /**
   * Obtener perfil del usuario autenticado
   */
  getProfile: async () => {
    const response = await apiClient.get('/users/profile')
    return response.data
  },

  /**
   * Actualizar perfil del usuario
   * @param {Object} data - Datos a actualizar
   */
  updateProfile: async (data) => {
    const response = await apiClient.patch('/users/profile', data)
    return response.data
  },

  /**
   * Logout (limpiar token)
   */
  logout: () => {
    authToken.remove()
    localStorage.removeItem('session_token')
  },
}





