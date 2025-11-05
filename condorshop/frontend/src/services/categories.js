import apiClient from './apiClient'

export const categoriesService = {
  /**
   * Obtener todas las categorías
   */
  getCategories: async () => {
    const response = await apiClient.get('/products/categories')
    return response.data
  },

  /**
   * Obtener categoría por slug
   * @param {string} slug - Slug de la categoría
   */
  getCategoryBySlug: async (slug) => {
    const response = await apiClient.get(`/products/categories`)
    const categories = Array.isArray(response.data) 
      ? response.data 
      : response.data.results || []
    return categories.find(cat => cat.slug === slug) || null
  },
}





