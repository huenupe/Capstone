import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const FREE_SHIPPING_THRESHOLD = 50000
const SHIPPING_COST = 5000

const calculateShipping = (subtotal) => {
  return subtotal >= FREE_SHIPPING_THRESHOLD ? 0 : SHIPPING_COST
}

export const useCartStore = create(
  persist(
    (set, get) => ({
      items: [],
      subtotal: 0,
      shipping: 0,
      total: 0,

      updateTotals: () => {
        const { items } = get()
        const subtotal = items.reduce(
          (sum, item) => sum + item.unit_price * item.quantity,
          0
        )
        const shipping = calculateShipping(subtotal)
        const total = subtotal + shipping

        set({ subtotal, shipping, total })
      },

      setCart: (cartData) => {
        const items = cartData.items || []
        const subtotal = items.reduce(
          (sum, item) => sum + item.unit_price * item.quantity,
          0
        )
        const shipping = calculateShipping(subtotal)
        const total = subtotal + shipping

        set({ items, subtotal, shipping, total })
      },

      addItem: (item) => {
        const { items } = get()
        const existingIndex = items.findIndex(
          (i) => i.product_id === item.product_id
        )

        let newItems
        if (existingIndex >= 0) {
          newItems = [...items]
          newItems[existingIndex] = {
            ...newItems[existingIndex],
            quantity: newItems[existingIndex].quantity + item.quantity,
          }
        } else {
          newItems = [...items, item]
        }

        set({ items: newItems })
        get().updateTotals()
      },

      updateItemQuantity: (itemId, quantity) => {
        const { items } = get()
        const newItems = items.map((item) =>
          item.id === itemId ? { ...item, quantity } : item
        )
        set({ items: newItems })
        get().updateTotals()
      },

      removeItem: (itemId) => {
        const { items } = get()
        const newItems = items.filter((item) => item.id !== itemId)
        set({ items: newItems })
        get().updateTotals()
      },

      clearCart: () => {
        set({ items: [], subtotal: 0, shipping: 0, total: 0 })
      },

      getItemCount: () => {
        const { items } = get()
        return items.reduce((sum, item) => sum + item.quantity, 0)
      },

      hasFreeShipping: () => {
        const { subtotal } = get()
        return subtotal >= FREE_SHIPPING_THRESHOLD
      },
    }),
    {
      name: 'cart-storage',
    }
  )
)





