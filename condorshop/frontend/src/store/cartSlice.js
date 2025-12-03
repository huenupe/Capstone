import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { cartService } from '../services/cart'

const FREE_SHIPPING_THRESHOLD = 50000
const SHIPPING_COST = 5000

const calculateShipping = (subtotal) => {
  return subtotal >= FREE_SHIPPING_THRESHOLD ? 0 : SHIPPING_COST
}

// Función de migración para normalizar datos corruptos
const migrateCartState = (state) => {
  if (!state || typeof state !== 'object') {
    return { items: [], subtotal: 0, shipping: 0, total: 0 }
  }

  // Validar items
  let items = Array.isArray(state.items) ? state.items : []
  items = items.filter(item => {
    return item && 
           typeof item === 'object' && 
           (item.product_id || item.id) && 
           typeof item.quantity === 'number' && 
           item.quantity > 0 &&
           typeof item.unit_price === 'number'
  })

  // Validar números
  const subtotal = typeof state.subtotal === 'number' && !isNaN(state.subtotal) ? state.subtotal : 0
  const shipping = typeof state.shipping === 'number' && !isNaN(state.shipping) ? state.shipping : 0
  const total = typeof state.total === 'number' && !isNaN(state.total) ? state.total : 0

  return { items, subtotal, shipping, total }
}

// Helper function para calcular valores derivados
const calculateDerivedValues = (items) => {
  const parseNumber = (value) => {
    if (value === null || value === undefined) return 0
    if (typeof value === 'number') return value
    if (typeof value === 'string') {
      const parsed = parseFloat(value)
      return isNaN(parsed) ? 0 : parsed
    }
    return 0
  }

  if (!Array.isArray(items) || items.length === 0) {
    return { subtotal: 0, shipping: 0, total: 0, totalDiscount: 0 }
  }

  const subtotal = items.reduce((sum, item) => {
    const price = parseNumber(item.unit_price)
    const qty = parseNumber(item.quantity)
    return sum + (price * qty)
  }, 0)

  const totalDiscount = items.reduce((sum, item) => {
    const originalPrice = parseNumber(item.product?.price || item.unit_price)
    const discountedPrice = parseNumber(item.unit_price)
    const qty = parseNumber(item.quantity)
    if (originalPrice > discountedPrice) {
      return sum + ((originalPrice - discountedPrice) * qty)
    }
    return sum
  }, 0)

  const shipping = calculateShipping(subtotal)
  const total = subtotal + shipping

  return { subtotal, shipping, total, totalDiscount }
}

export const useCartStore = create(
  persist(
    (set, get) => ({
      items: [],
      // Valores derivados calculados automáticamente (NO se persisten en localStorage)
      // Se recalcularán cada vez que cambien los items
      subtotal: 0,
      shipping: 0,
      total: 0,
      totalDiscount: 0,
      
      // Estados de carga y sincronización
      isLoading: false,
      fetchInProgress: false,
      lastFetched: null,
      error: null,

      // Calcular valores derivados automáticamente basados en items
      updateTotals: () => {
        const { items } = get()
        const derived = calculateDerivedValues(items)
        set(derived)
      },
      
      /**
       * Fetch centralizado del carrito desde la API
       * Protegido contra múltiples llamadas simultáneas
       * ✅ MEJORA: Funciona tanto para usuarios autenticados como invitados (guests)
       * @param {boolean} force - Forzar fetch incluso si ya hay uno en progreso
       * @returns {Promise<void>}
       */
      fetchCart: async (force = false) => {
        const { fetchInProgress } = get()
        
        // Evitar múltiples fetches simultáneos (a menos que se fuerce)
        if (fetchInProgress && !force) {
          if (import.meta.env.DEV) {
            console.log('[cartStore] fetchCart ya en progreso, omitiendo...')
          }
          return
        }
        
        set({ fetchInProgress: true, isLoading: true, error: null })
        
        try {
          if (import.meta.env.DEV) {
            console.time('GET /api/cart/ (store)')
          }
          
          const cartData = await cartService.getCart()
          
          if (import.meta.env.DEV) {
            console.timeEnd('GET /api/cart/ (store)')
            console.log('[cartStore] Cart fetched:', cartData)
          }
          
          const items = Array.isArray(cartData?.items) ? cartData.items : []
          
          // ✅ VALIDACIÓN: Detectar duplicados de id en DEV
          if (import.meta.env.DEV) {
            const ids = items.map(i => i.id)
            const duplicates = ids.filter((id, index) => ids.indexOf(id) !== index)
            if (duplicates.length > 0) {
              console.error('[cartStore] ⚠️ DUPLICADOS DETECTADOS en fetchCart:', duplicates)
              console.log('[cartStore] Items recibidos:', items.map(i => ({ id: i.id, product_id: i.product?.id, product_name: i.product?.name })))
            } else {
              console.log('[cartStore] Items ids después de fetch:', ids)
            }
          }
          
          const derived = calculateDerivedValues(items)
          
          set({
            items,
            ...derived,
            lastFetched: Date.now(),
            error: null,
          })
        } catch (error) {
          console.error('[cartStore] Error fetching cart:', error)
          
          // ✅ MEJORA: Solo limpiar si es 401/403 Y hay token (usuario autenticado perdió sesión)
          const accessToken = localStorage.getItem('accessToken')
          const status = error.response?.status
          if ((status === 401 || status === 403) && accessToken) {
            // Usuario autenticado perdió sesión → limpiar token y carrito
            localStorage.removeItem('accessToken')
            get().clearCart()
            if (import.meta.env.DEV) {
              console.log('[cartStore] Error 401/403 con token, limpiando carrito y token')
            }
          }
          // Si es guest (sin token) y hay error, mantener carrito local (no limpiar)
          
          set({ error: error.response?.data?.error || 'Error al cargar el carrito' })
          throw error
        } finally {
          set({ fetchInProgress: false, isLoading: false })
        }
      },
      
      /**
       * Sincronizar carrito con API (alias de fetchCart para claridad semántica)
       */
      syncCart: async () => {
        return get().fetchCart()
      },

      setCart: (cartData) => {
        try {
          const items = Array.isArray(cartData?.items) ? cartData.items : []
          
          // Convertir strings a números si es necesario (Django Decimal puede venir como string)
          const parseNumber = (value) => {
            if (value === null || value === undefined) return 0
            if (typeof value === 'number') return value
            if (typeof value === 'string') {
              const parsed = parseFloat(value)
              return isNaN(parsed) ? 0 : parsed
            }
            return 0
          }
          
          // Calcular valores derivados automáticamente
          const derived = calculateDerivedValues(items)
          set({ items, ...derived })
        } catch (error) {
          console.error('Error in setCart:', error)
          set({ items: [], subtotal: 0, shipping: 0, total: 0, totalDiscount: 0 })
        }
      },

      addItem: (item) => {
        try {
          if (!item || (!item.product_id && !item.id)) {
            return
          }

          const { items } = get()
          const safeItems = Array.isArray(items) ? items : []
          const existingIndex = safeItems.findIndex(
            (i) => (i.product_id || i.id) === (item.product_id || item.id)
          )

          let newItems
          if (existingIndex >= 0) {
            newItems = [...safeItems]
            const existingItem = newItems[existingIndex]
            newItems[existingIndex] = {
              ...existingItem,
              quantity: (existingItem.quantity || 0) + (item.quantity || 1),
            }
          } else {
            newItems = [...safeItems, item]
          }

          const derived = calculateDerivedValues(newItems)
          set({ items: newItems, ...derived })
        } catch (error) {
          if (import.meta.env.DEV) {
            console.error('[cartStore] Error adding item:', error)
          }
        }
      },

      updateItemQuantity: (itemId, quantity) => {
        try {
          const { items } = get()
          if (!Array.isArray(items)) {
            return
          }

          const safeQty = typeof quantity === 'number' && quantity > 0 ? quantity : 0
          // ✅ CORRECCIÓN: Solo actualizar por item.id (único), NO por product_id
          const newItems = items.map((item) =>
            item.id === itemId ? { ...item, quantity: safeQty } : item
          ).filter(item => item.quantity > 0)

          const derived = calculateDerivedValues(newItems)
          set({ items: newItems, ...derived })
        } catch (error) {
          if (import.meta.env.DEV) {
            console.error('[cartStore] Error updating item quantity:', error)
          }
        }
      },

      /**
       * Actualizar un item específico con la respuesta del backend
       * Usa la respuesta del backend para actualizar el item y recalcular totales
       * ✅ CORRECCIÓN: Solo actualizar por item.id, NO por product_id (evita duplicar items)
       * @param {Object} updatedItem - Item actualizado del backend
       */
      updateItemFromBackend: (updatedItem) => {
        try {
          const { items } = get()
          if (!Array.isArray(items) || !updatedItem || !updatedItem.id) {
            if (import.meta.env.DEV) {
              console.warn('[cartStore] updateItemFromBackend: invalid updatedItem', updatedItem)
            }
            return
          }

          // ✅ CORRECCIÓN: Solo actualizar por item.id (único), NO por product_id
          // Si hay múltiples items del mismo producto, solo actualizamos el que coincide por id
          const newItems = items.map((item) => {
            if (item.id === updatedItem.id) {
              return {
                ...item,
                ...updatedItem,
                // Asegurar que quantity y unit_price sean números
                quantity: typeof updatedItem.quantity === 'number' ? updatedItem.quantity : parseFloat(updatedItem.quantity) || item.quantity,
                unit_price: typeof updatedItem.unit_price === 'number' ? updatedItem.unit_price : parseFloat(updatedItem.unit_price) || item.unit_price,
              }
            }
            return item
          }).filter(item => item.quantity > 0)

          // ✅ VALIDACIÓN: Detectar duplicados de id en DEV
          if (import.meta.env.DEV) {
            const ids = newItems.map(i => i.id)
            const duplicates = ids.filter((id, index) => ids.indexOf(id) !== index)
            if (duplicates.length > 0) {
              console.error('[cartStore] ⚠️ DUPLICADOS DETECTADOS después de updateItemFromBackend:', duplicates)
            }
          }

          const derived = calculateDerivedValues(newItems)
          set({ items: newItems, ...derived })
        } catch (error) {
          console.error('[cartStore] Error updating item from backend:', error)
        }
      },

      removeItem: (itemId) => {
        try {
          const { items } = get()
          if (!Array.isArray(items)) {
            return
          }

          // ✅ CORRECCIÓN: Solo eliminar por item.id (único), NO por product_id
          const newItems = items.filter((item) => item.id !== itemId)
          const derived = calculateDerivedValues(newItems)
          set({ items: newItems, ...derived })
        } catch (error) {
          if (import.meta.env.DEV) {
            console.error('[cartStore] Error removing item:', error)
          }
        }
      },

      clearCart: () => {
        // ✅ MEJORA: Resetear completamente el carrito incluyendo estados derivados
        set({ 
          items: [], 
          subtotal: 0, 
          shipping: 0, 
          total: 0, 
          totalDiscount: 0,
          error: null,
          lastFetched: null,
        })
      },

      getItemCount: () => {
        try {
          const { items } = get()
          if (!Array.isArray(items)) {
            return 0
          }
          return items.reduce((sum, item) => {
            const qty = typeof item.quantity === 'number' ? item.quantity : 0
            return sum + qty
          }, 0)
        } catch (error) {
          return 0
        }
      },

      hasFreeShipping: () => {
        try {
          const { subtotal } = get()
          return typeof subtotal === 'number' && subtotal >= FREE_SHIPPING_THRESHOLD
        } catch (error) {
          return false
        }
      },
    }),
    {
      name: 'cart-storage',
      // Solo persistir 'items' - los valores calculados (subtotal, shipping, total, totalDiscount) 
      // NO se guardan para reducir tamaño de localStorage y mejor rendimiento
      partialize: (state) => ({ items: state.items }),
      migrate: (persistedState) => {
        const migrated = migrateCartState(persistedState)
        // Solo retornar items - los valores derivados se calcularán automáticamente
        const items = migrated.items || []
        const derived = calculateDerivedValues(items)
        return { items, ...derived }
      },
    }
  )
)





