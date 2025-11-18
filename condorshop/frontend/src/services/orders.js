import apiClient from './apiClient'
import { useAuthStore } from '../store/authSlice'

export const ordersService = {
  /**
   * Crear orden desde el carrito
   * @param {Object} data - Datos del pedido (customer, address, etc.)
   * POST /api/checkout/create según backend
   */
  createOrder: async (data) => {
    const response = await apiClient.post('/checkout/create', data)
    return response.data
  },

  /**
   * Obtener cotización de envío
   * @param {Object} data - { region, cart_items: [{ product_id, quantity }], subtotal }
   * POST /api/checkout/shipping-quote
   */
  getShippingQuote: async (data) => {
    const response = await apiClient.post('/checkout/shipping-quote', data)
    return response.data
  },

  /**
   * Obtener historial de órdenes del usuario
   * GET /api/orders/ - Historial del usuario autenticado
   */
  getUserOrders: async () => {
    const { user } = useAuthStore.getState()
    
    if (!user) {
      throw new Error('Usuario no autenticado')
    }
    
    // Endpoint correcto según backend: /api/orders/
    const response = await apiClient.get('/orders/')
    return Array.isArray(response.data) ? response.data : response.data.results || []
  },

  /**
   * Cancelar un pedido en estado PENDING
   * POST /api/orders/{orderId}/cancel/
   */
  cancelOrder: async (orderId) => {
    const response = await apiClient.post(`/orders/${orderId}/cancel/`)
    return response.data
  },
}

