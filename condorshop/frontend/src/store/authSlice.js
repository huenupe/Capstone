import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authToken } from '../utils/authToken'

// Función de migración para normalizar datos corruptos
const migrateAuthState = (state) => {
  if (!state || typeof state !== 'object') {
    return { token: null, user: null, role: null, isAuthenticated: false }
  }

  const token = typeof state.token === 'string' && state.token.length > 0 ? state.token : null
  const user = state.user && typeof state.user === 'object' ? state.user : null
  const role = typeof state.role === 'string' ? state.role : null
  const isAuthenticated = typeof state.isAuthenticated === 'boolean' ? state.isAuthenticated : false

  // Si hay token pero no user, mantener token pero no autenticado
  const safeIsAuthenticated = isAuthenticated && token && user

  return { token, user, role, isAuthenticated: safeIsAuthenticated }
}

export const useAuthStore = create(
  persist(
    (set) => ({
      token: null,
      user: null,
      role: null,
      isAuthenticated: false,

      login: (user, token) => {
        try {
          if (!user || !token) {
            return
          }

          authToken.set(token)
          set({
            token: typeof token === 'string' ? token : null,
            user: user && typeof user === 'object' ? user : null,
            role: user?.role || null,
            isAuthenticated: true,
          })
        } catch (error) {
          // Ignorar errores de login
        }
      },

      logout: () => {
        try {
          authToken.remove()
          set({
            token: null,
            user: null,
            role: null,
            isAuthenticated: false,
          })
        } catch (error) {
          // Ignorar errores de logout
        }
      },

      updateUser: (user) => {
        try {
          if (!user || typeof user !== 'object') {
            return
          }

          set({
            user,
            role: user?.role || null,
          })
        } catch (error) {
          // Ignorar errores de actualización
        }
      },

      initialize: () => {
        try {
          const token = authToken.get()
          if (token && typeof token === 'string') {
            set({ token, isAuthenticated: true })
          }
        } catch (error) {
          // Ignorar errores de inicialización
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        role: state.role,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
      migrate: (persistedState) => {
        return migrateAuthState(persistedState)
      },
    }
  )
)





