/**
 * Utilidades para manejo de tokens de autenticación
 */

const TOKEN_KEY = 'auth_token'

export const authToken = {
  get: () => {
    return localStorage.getItem(TOKEN_KEY)
  },

  set: (token) => {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  },

  remove: () => {
    localStorage.removeItem(TOKEN_KEY)
  },

  exists: () => {
    return !!localStorage.getItem(TOKEN_KEY)
  },
}





