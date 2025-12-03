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
            if (import.meta.env.DEV) {
              console.warn('[authStore] Login: user o token faltante')
            }
            return
          }

          authToken.set(token)
          set({
            token: typeof token === 'string' ? token : null,
            user: user && typeof user === 'object' ? user : null,
            role: user?.role || null,
            isAuthenticated: true,
          })
          
          if (import.meta.env.DEV) {
            console.log('[authStore] Login exitoso para:', user?.email || user?.id)
          }
        } catch (error) {
          if (import.meta.env.DEV) {
            console.error('[authStore] Error en login:', error)
          }
        }
      },

      logout: () => {
        try {
          // ✅ MEJORA: NO limpiar carrito - debe funcionar como guest después de logout
          // El carrito seguirá funcionando con session_token
          
          // ✅ MEJORA: Limpiar órdenes al hacer logout usando import() dinámico (compatible con Vite)
          // Usamos import() en lugar de require() porque Vite/React no soporta require en el navegador
          import('../store/ordersSlice')
            .then(({ useOrdersStore }) => {
              if (useOrdersStore && typeof useOrdersStore.getState === 'function') {
                const clearOrders = useOrdersStore.getState().clearOrders
                if (typeof clearOrders === 'function') {
                  clearOrders()
                  if (import.meta.env.DEV) {
                    console.log('[authStore] Órdenes limpiadas correctamente')
                  }
                }
              }
            })
            .catch((err) => {
              // No crítico si ordersSlice no existe o falla la importación
              if (import.meta.env.DEV) {
                console.log('[authStore] No se pudo limpiar órdenes (no crítico):', err.message)
              }
            })
          
          // ✅ CRÍTICO: Eliminar token y actualizar estado SIEMPRE
          authToken.remove()
          
          // ✅ CRÍTICO: Actualizar estado SIEMPRE (no esperar a la limpieza de órdenes)
          set({
            token: null,
            user: null,
            role: null,
            isAuthenticated: false,
          })
          
          if (import.meta.env.DEV) {
            console.log('[authStore] Logout exitoso')
          }
        } catch (error) {
          // ✅ MEJORA: Loguear errores en desarrollo
          if (import.meta.env.DEV) {
            console.error('[authStore] Error en logout:', error)
          }
          
          // ✅ CRÍTICO: Asegurar que el estado se actualice incluso si hay errores
          authToken.remove()
          set({
            token: null,
            user: null,
            role: null,
            isAuthenticated: false,
          })
        }
      },

      updateUser: (user) => {
        try {
          if (!user || typeof user !== 'object') {
            if (import.meta.env.DEV) {
              console.warn('[authStore] updateUser: user inválido')
            }
            return
          }

          set({
            user,
            role: user?.role || null,
          })
        } catch (error) {
          if (import.meta.env.DEV) {
            console.error('[authStore] Error en updateUser:', error)
          }
        }
      },

      initialize: () => {
        try {
          const token = authToken.get()
          if (token && typeof token === 'string') {
            set({ token, isAuthenticated: true })
            if (import.meta.env.DEV) {
              console.log('[authStore] Inicializado con token existente')
            }
          } else {
            if (import.meta.env.DEV) {
              console.log('[authStore] Inicializado sin token (usuario no autenticado)')
            }
          }
        } catch (error) {
          if (import.meta.env.DEV) {
            console.error('[authStore] Error en initialize:', error)
          }
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





