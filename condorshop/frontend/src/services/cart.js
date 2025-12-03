import apiClient from './apiClient'

export const cartService = {
  /**
   * Obtener carrito
   */
  getCart: async () => {
    if (import.meta.env.DEV) {
      console.time('GET /api/cart/')
    }
    try {
      const response = await apiClient.get('/cart/')
      if (import.meta.env.DEV) {
        console.timeEnd('GET /api/cart/')
        console.log('[cartService] Cart data:', response.data)
      }
      return response.data
    } catch (error) {
      if (import.meta.env.DEV) {
        console.timeEnd('GET /api/cart/')
        console.error('[cartService] Error fetching cart:', error)
      }
      throw error
    }
  },

  /**
   * Agregar producto al carrito
   * @param {Object} data - { product_id, quantity }
   */
  addToCart: async (data) => {
    if (import.meta.env.DEV) {
      console.time('POST /api/cart/add')
    }
    try {
      const response = await apiClient.post('/cart/add', data)
      if (import.meta.env.DEV) {
        console.timeEnd('POST /api/cart/add')
        console.log('[cartService] Add to cart response:', response.data)
      }
      return response.data
    } catch (error) {
      if (import.meta.env.DEV) {
        console.timeEnd('POST /api/cart/add')
        console.error('[cartService] Error adding to cart:', error)
      }
      throw error
    }
  },

  /**
   * Actualizar cantidad de un item del carrito
   * @param {number} itemId - ID del item
   * @param {Object} data - { quantity }
   */
  updateCartItem: async (itemId, data) => {
    if (import.meta.env.DEV) {
      console.time(`PATCH /api/cart/items/${itemId}`)
    }
    try {
      const response = await apiClient.patch(`/cart/items/${itemId}`, data)
      if (import.meta.env.DEV) {
        console.timeEnd(`PATCH /api/cart/items/${itemId}`)
        console.log('[cartService] Update cart item response:', response.data)
      }
      return response.data
    } catch (error) {
      if (import.meta.env.DEV) {
        console.timeEnd(`PATCH /api/cart/items/${itemId}`)
        console.error('[cartService] Error updating cart item:', error)
      }
      throw error
    }
  },

  /**
   * Eliminar item del carrito
   * @param {number} itemId - ID del item
   */
  removeCartItem: async (itemId) => {
    if (import.meta.env.DEV) {
      console.time(`DELETE /api/cart/items/${itemId}/delete`)
    }
    try {
      const response = await apiClient.delete(`/cart/items/${itemId}/delete`)
      if (import.meta.env.DEV) {
        console.timeEnd(`DELETE /api/cart/items/${itemId}/delete`)
        console.log('[cartService] Remove cart item response:', response.data)
      }
      return response.data
    } catch (error) {
      if (import.meta.env.DEV) {
        console.timeEnd(`DELETE /api/cart/items/${itemId}/delete`)
        console.error('[cartService] Error removing cart item:', error)
      }
      throw error
    }
  },
}





