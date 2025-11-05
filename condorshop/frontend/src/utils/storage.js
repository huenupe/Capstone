/**
 * Utilidades para localStorage y sessionStorage
 */

export const storage = {
  get: (key, useSessionStorage = false) => {
    try {
      const storageType = useSessionStorage ? sessionStorage : localStorage
      const item = storageType.getItem(key)
      return item ? JSON.parse(item) : null
    } catch (error) {
      console.error(`Error reading ${key} from ${useSessionStorage ? 'sessionStorage' : 'localStorage'}:`, error)
      return null
    }
  },

  set: (key, value, useSessionStorage = false) => {
    try {
      const storageType = useSessionStorage ? sessionStorage : localStorage
      storageType.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.error(`Error saving ${key} to ${useSessionStorage ? 'sessionStorage' : 'localStorage'}:`, error)
    }
  },

  remove: (key, useSessionStorage = false) => {
    try {
      const storageType = useSessionStorage ? sessionStorage : localStorage
      storageType.removeItem(key)
    } catch (error) {
      console.error(`Error removing ${key} from ${useSessionStorage ? 'sessionStorage' : 'localStorage'}:`, error)
    }
  },

  clear: (useSessionStorage = false) => {
    try {
      const storageType = useSessionStorage ? sessionStorage : localStorage
      storageType.clear()
    } catch (error) {
      console.error(`Error clearing ${useSessionStorage ? 'sessionStorage' : 'localStorage'}:`, error)
    }
  },
}





