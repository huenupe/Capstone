import apiClient from './apiClient'

export const cartService = {
  /**
   * Obtener carrito
   */
  getCart: async () => {
    const response = await apiClient.get('/cart')
    return response.data
  },

  /**
   * Agregar producto al carrito
   * @param {Object} data - { product_id, quantity }
   */
  addToCart: async (data) => {
    const response = await apiClient.post('/cart/add', data)
    return response.data
  },

  /**
   * Actualizar cantidad de un item del carrito
   * @param {number} itemId - ID del item
   * @param {Object} data - { quantity }
   */
  updateCartItem: async (itemId, data) => {
    const response = await apiClient.patch(`/cart/items/${itemId}`, data)
    return response.data
  },

  /**
   * Eliminar item del carrito
   * @param {number} itemId - ID del item
   */
  removeCartItem: async (itemId) => {
    const response = await apiClient.delete(`/cart/items/${itemId}/delete`)
    return response.data
  },
}





