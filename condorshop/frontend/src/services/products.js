import apiClient from './apiClient'
import publicApiClient from './publicApiClient'

export const productsService = {
  /**
   * Obtener lista de productos con filtros y paginación
   * @param {Object} params - { search, category, min_price, max_price, ordering, page, page_size }
   */
  getProducts: async (params = {}) => {
    const response = await publicApiClient.get('/products/', { params })
    return response.data
  },

  /**
   * Obtener producto por slug
   * @param {string} slug - Slug del producto
   */
  getProductBySlug: async (slug) => {
    const response = await publicApiClient.get(`/products/${slug}/`)
    return response.data
  },

  /**
   * Obtener categorías
   */
  getCategories: async () => {
    const response = await publicApiClient.get('/products/categories')
    return response.data
  },
}





