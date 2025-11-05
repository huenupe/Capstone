import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authToken } from '../utils/authToken'

export const useAuthStore = create(
  persist(
    (set) => ({
      token: null,
      user: null,
      role: null,
      isAuthenticated: false,

      login: (user, token) => {
        authToken.set(token)
        set({
          token,
          user,
          role: user?.role || null,
          isAuthenticated: true,
        })
      },

      logout: () => {
        authToken.remove()
        set({
          token: null,
          user: null,
          role: null,
          isAuthenticated: false,
        })
      },

      updateUser: (user) => {
        set({
          user,
          role: user?.role || null,
        })
      },

      initialize: () => {
        const token = authToken.get()
        if (token) {
          set({ token, isAuthenticated: true })
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
    }
  )
)





