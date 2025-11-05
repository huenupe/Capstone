/**
 * Utilidades para localStorage y sessionStorage
 * Manejo seguro de datos con validación y defaults
 */

export const storage = {
  get: (key, useSessionStorage = false, defaultValue = null) => {
    try {
      if (typeof window === 'undefined') {
        return defaultValue
      }
      
      const storageType = useSessionStorage ? sessionStorage : localStorage
      const item = storageType.getItem(key)
      
      if (!item) {
        return defaultValue
      }
      
      try {
        const parsed = JSON.parse(item)
        return parsed !== null && parsed !== undefined ? parsed : defaultValue
      } catch (parseError) {
        // JSON inválido, limpiar y retornar default
        storageType.removeItem(key)
        return defaultValue
      }
    } catch (error) {
      // Error de acceso al storage, retornar default
      return defaultValue
    }
  },

  set: (key, value, useSessionStorage = false) => {
    try {
      if (typeof window === 'undefined') {
        return false
      }
      
      const storageType = useSessionStorage ? sessionStorage : localStorage
      const serialized = JSON.stringify(value)
      storageType.setItem(key, serialized)
      return true
    } catch (error) {
      // Storage puede estar lleno o deshabilitado
      return false
    }
  },

  remove: (key, useSessionStorage = false) => {
    try {
      if (typeof window === 'undefined') {
        return
      }
      
      const storageType = useSessionStorage ? sessionStorage : localStorage
      storageType.removeItem(key)
    } catch (error) {
      // Ignorar errores de remoción
    }
  },

  clear: (useSessionStorage = false) => {
    try {
      if (typeof window === 'undefined') {
        return
      }
      
      const storageType = useSessionStorage ? sessionStorage : localStorage
      storageType.clear()
    } catch (error) {
      // Ignorar errores de limpieza
    }
  },
}





