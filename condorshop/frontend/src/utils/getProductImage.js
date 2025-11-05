/**
 * Obtiene la URL de la imagen principal de un producto
 * Maneja tanto productos de lista (main_image) como de detalle (images[0].image)
 * 
 * @param {Object} product - Objeto producto del backend
 * @returns {string} URL de la imagen o placeholder
 */
export const getProductImage = (product) => {
  if (!product) {
    return '/placeholder-product.jpg'
  }

  // ProductListSerializer devuelve main_image
  if (product.main_image) {
    return product.main_image
  }

  // ProductDetailSerializer devuelve images con campo image
  if (product.images && product.images.length > 0) {
    const firstImage = product.images[0]
    return firstImage.image || firstImage.url || '/placeholder-product.jpg'
  }

  return '/placeholder-product.jpg'
}

