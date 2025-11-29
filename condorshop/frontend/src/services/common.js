import apiClient from './apiClient'
import publicApiClient from './publicApiClient'

export const commonService = {
  /**
   * Obtener slides activos del carrusel principal
   * @returns {Promise<Array>} Array de slides con id, name, description, image_url, alt_text, order
   * @throws {Error} Si la petición falla o los datos son inválidos
   */
  getHeroCarouselSlides: async () => {
    try {
      const response = await publicApiClient.get('/common/hero-carousel/')
      
      // Validar que la respuesta sea un array
      if (!Array.isArray(response.data)) {
        console.warn('[commonService] getHeroCarouselSlides: respuesta no es un array', response.data)
        return []
      }
      
      // Filtrar slides válidos (deben tener image_url)
      const validSlides = response.data.filter(slide => 
        slide && slide.image_url && typeof slide.image_url === 'string'
      )
      
      if (validSlides.length === 0 && response.data.length > 0) {
        console.warn('[commonService] getHeroCarouselSlides: ningún slide tiene image_url válido')
      }
      
      return validSlides
    } catch (error) {
      console.error('[commonService] getHeroCarouselSlides error:', error)
      // Re-lanzar el error para que el componente pueda manejarlo
      throw error
    }
  },
}

