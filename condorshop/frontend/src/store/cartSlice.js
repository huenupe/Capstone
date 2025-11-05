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

export const useCartStore = create(
  persist(
    (set, get) => ({
      items: [],
      subtotal: 0,
      shipping: 0,
      total: 0,
      totalDiscount: 0,

      updateTotals: () => {
        try {
          const { items } = get()
          if (!Array.isArray(items)) {
            set({ items: [], subtotal: 0, shipping: 0, total: 0, totalDiscount: 0 })
            return
          }

          // Función para parsear números (Django Decimal puede venir como string)
          const parseNumber = (value) => {
            if (value === null || value === undefined) return 0
            if (typeof value === 'number') return value
            if (typeof value === 'string') {
              const parsed = parseFloat(value)
              return isNaN(parsed) ? 0 : parsed
            }
            return 0
          }

          const subtotal = items.reduce(
            (sum, item) => {
              const price = parseNumber(item.unit_price)
              const qty = parseNumber(item.quantity)
              const itemSubtotal = price * qty
              return sum + itemSubtotal
            },
            0
          )
          
          // Calcular descuento total (diferencia entre precio original y precio con descuento)
          const totalDiscount = items.reduce(
            (sum, item) => {
              const originalPrice = parseNumber(item.product?.price || item.unit_price)
              const discountedPrice = parseNumber(item.unit_price)
              const qty = parseNumber(item.quantity)
              if (originalPrice > discountedPrice) {
                return sum + ((originalPrice - discountedPrice) * qty)
              }
              return sum
            },
            0
          )
          
          const shipping = calculateShipping(subtotal)
          const total = subtotal + shipping

          set({ subtotal, shipping, total, totalDiscount })
        } catch (error) {
          console.error('Error in updateTotals:', error)
          set({ items: [], subtotal: 0, shipping: 0, total: 0, totalDiscount: 0 })
        }
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
          
          // Calcular subtotal desde items (siempre calcular desde items para asegurar precisión)
          let subtotal = 0
          if (items.length > 0) {
            subtotal = items.reduce(
              (sum, item) => {
                const price = parseNumber(item.unit_price)
                const qty = parseNumber(item.quantity)
                const itemSubtotal = price * qty
                return sum + itemSubtotal
              },
              0
            )
          } else if (cartData?.subtotal !== null && cartData?.subtotal !== undefined) {
            // Solo usar subtotal del backend si no hay items
            subtotal = parseNumber(cartData.subtotal)
          }
          
          // Calcular descuento total
          let totalDiscount = 0
          if (items.length > 0) {
            totalDiscount = items.reduce(
              (sum, item) => {
                const originalPrice = parseNumber(item.product?.price || item.unit_price)
                const discountedPrice = parseNumber(item.unit_price)
                const qty = parseNumber(item.quantity)
                if (originalPrice > discountedPrice) {
                  return sum + ((originalPrice - discountedPrice) * qty)
                }
                return sum
              },
              0
            )
          }
          
          // Usar shipping_cost del backend si está disponible, sino calcularlo
          let shipping = 0
          if (cartData?.shipping_cost !== null && cartData?.shipping_cost !== undefined) {
            shipping = parseNumber(cartData.shipping_cost)
          } else {
            shipping = calculateShipping(subtotal)
          }
          
          // Usar total del backend si está disponible, sino calcularlo
          let total = 0
          if (cartData?.total !== null && cartData?.total !== undefined) {
            total = parseNumber(cartData.total)
          } else {
            total = subtotal + shipping
          }

          set({ items, subtotal, shipping, total, totalDiscount })
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

          set({ items: newItems })
          get().updateTotals()
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

          set({ items: newItems })
          get().updateTotals()
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
          set({ items: newItems })
          get().updateTotals()
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
      migrate: (persistedState, version) => {
        return migrateCartState(persistedState)
      },
    }
  )
)





