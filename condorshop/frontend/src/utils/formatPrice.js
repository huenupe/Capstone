/**
 * Formatea un precio en pesos chilenos
 * @param {number} price - Precio a formatear
 * @returns {string} - Precio formateado (ej: "$50.000")
 */
export const formatPrice = (price) => {
  if (price === null || price === undefined || isNaN(price)) {
    return '$0'
  }
  
  return new Intl.NumberFormat('es-CL', {
    style: 'currency',
    currency: 'CLP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(price)
}





