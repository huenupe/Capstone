/**
 * Utilidades para manejo de tokens de autenticación
 * Manejo seguro con validación y tolerancia a errores
 */

const TOKEN_KEY = 'auth_token'

export const authToken = {
  get: () => {
    try {
      if (typeof window === 'undefined' || !localStorage) {
        return null
      }
      const token = localStorage.getItem(TOKEN_KEY)
      return typeof token === 'string' && token.length > 0 ? token : null
    } catch (error) {
      return null
    }
  },

  set: (token) => {
    try {
      if (typeof window === 'undefined' || !localStorage) {
        return false
      }

      if (token && typeof token === 'string' && token.length > 0) {
        localStorage.setItem(TOKEN_KEY, token)
        return true
      } else {
        localStorage.removeItem(TOKEN_KEY)
        return true
      }
    } catch (error) {
      // Storage puede estar lleno o deshabilitado
      return false
    }
  },

  remove: () => {
    try {
      if (typeof window === 'undefined' || !localStorage) {
        return
      }
      localStorage.removeItem(TOKEN_KEY)
    } catch (error) {
      // Ignorar errores de remoción
    }
  },

  exists: () => {
    try {
      if (typeof window === 'undefined' || !localStorage) {
        return false
      }
      return !!localStorage.getItem(TOKEN_KEY)
    } catch (error) {
      return false
    }
  },
}





