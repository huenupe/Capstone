import { create } from 'zustand'
import { persist } from 'zustand/middleware'

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

      // Calcular valores derivados automáticamente basados en items
      updateTotals: () => {
        const { items } = get()
        const derived = calculateDerivedValues(items)
        set(derived)
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
          // Ignorar errores de agregar item
        }
      },

      updateItemQuantity: (itemId, quantity) => {
        try {
          const { items } = get()
          if (!Array.isArray(items)) {
            return
          }

          const safeQty = typeof quantity === 'number' && quantity > 0 ? quantity : 0
          const newItems = items.map((item) =>
            (item.id === itemId || item.product_id === itemId) ? { ...item, quantity: safeQty } : item
          ).filter(item => item.quantity > 0)

          const derived = calculateDerivedValues(newItems)
          set({ items: newItems, ...derived })
        } catch (error) {
          // Ignorar errores de actualización
        }
      },

      removeItem: (itemId) => {
        try {
          const { items } = get()
          if (!Array.isArray(items)) {
            return
          }

          const newItems = items.filter((item) => 
            (item.id !== itemId && item.product_id !== itemId)
          )
          const derived = calculateDerivedValues(newItems)
          set({ items: newItems, ...derived })
        } catch (error) {
          // Ignorar errores de remoción
        }
      },

      clearCart: () => {
        set({ items: [], subtotal: 0, shipping: 0, total: 0, totalDiscount: 0 })
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





