import { create } from 'zustand'

/**
 * Store para manejar el estado del checkout
 * - paymentMethod: método de pago seleccionado ('webpay' | 'other')
 * - canPay: flag para habilitar/deshabilitar el botón de pago
 * - deliveryMethod: método de entrega seleccionado ('pickup' | 'delivery')
 * - couponCode: código de cupón aplicado
 */
export const useCheckoutStore = create((set) => ({
  paymentMethod: 'webpay',
  canPay: false, // Siempre false por ahora (placeholder)
  deliveryMethod: null,
  couponCode: null,
  discounts: 0,

  setPaymentMethod: (method) => set({ paymentMethod: method }),
  
  setCanPay: (canPay) => set({ canPay }),
  
  setDeliveryMethod: (method) => set({ deliveryMethod: method }),
  
  setCouponCode: (code) => set({ couponCode: code }),
  
  setDiscounts: (amount) => set({ discounts: amount }),
  
  reset: () => set({
    paymentMethod: 'webpay',
    canPay: false,
    deliveryMethod: null,
    couponCode: null,
    discounts: 0,
  }),
}))

