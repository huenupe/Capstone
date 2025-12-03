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
   * Obtener historial de órdenes del usuario con paginación
   * GET /api/orders/?page=1&page_size=20
   * @param {Object} params - { page: 1, page_size: 20 }
   * @returns {Promise<Object>} - { results: [], count, next, previous }
   */
  getUserOrders: async (params = {}) => {
    const { user } = useAuthStore.getState()
    
    if (!user) {
      throw new Error('Usuario no autenticado')
    }
    
    // Endpoint con paginación
    const queryParams = new URLSearchParams()
    if (params.page) queryParams.append('page', params.page)
    if (params.page_size) queryParams.append('page_size', params.page_size)
    
    const url = `/orders/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    const response = await apiClient.get(url)
    
    // Si la respuesta tiene paginación (count, next, previous), devolverla completa
    if (response.data.count !== undefined) {
      return response.data
    }
    
    // Fallback: si no hay paginación, devolver como array
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

