import { formatPrice } from '../../utils/formatPrice'

const PriceTag = ({ 
  price, 
  originalPrice, 
  discountPercent,
  className = '',
  size = 'lg' // 'sm' | 'md' | 'lg'
}) => {
  // Validar que price y originalPrice sean números válidos
  const priceNum = typeof price === 'number' ? price : parseFloat(price) || 0
  const originalPriceNum = originalPrice && typeof originalPrice === 'number' ? originalPrice : (originalPrice ? parseFloat(originalPrice) : null)
  
  // Solo mostrar descuento si:
  // 1. Hay un originalPrice válido
  // 2. El precio actual es mayor que 0
  // 3. El precio actual es menor que el original
  // 4. El descuento calculado es mayor que 0
  const hasDiscount = originalPriceNum && priceNum > 0 && originalPriceNum > priceNum
  const discount = hasDiscount ? (discountPercent || Math.round(((originalPriceNum - priceNum) / originalPriceNum) * 100)) : 0
  
  // Si el descuento es 0 o el precio es 0, no mostrar descuento
  const showDiscount = hasDiscount && discount > 0 && priceNum > 0

  // Tamaños de texto según el prop size
  const sizeClasses = {
    sm: {
      newPrice: 'text-base font-bold',
      oldPrice: 'text-sm',
      badge: 'text-xs px-1.5 py-0.5'
    },
    md: {
      newPrice: 'text-xl font-bold',
      oldPrice: 'text-base',
      badge: 'text-xs px-2 py-0.5'
    },
    lg: {
      newPrice: 'text-2xl font-bold',
      oldPrice: 'text-lg',
      badge: 'text-sm px-2 py-1'
    }
  }

  const classes = sizeClasses[size] || sizeClasses.lg

  return (
    <div className={`flex flex-col ${className}`}>
      {showDiscount ? (
        <>
          {/* Precio nuevo arriba con badge de descuento */}
          <div className="flex items-center gap-2 mb-1">
            <span className={`${classes.newPrice} text-red-600`}>
              {formatPrice(priceNum)}
            </span>
            <span className={`${classes.badge} font-semibold text-white bg-red-600 rounded`}>
              -{discount}%
            </span>
          </div>
          {/* Precio antiguo tachado abajo */}
          <span className={`${classes.oldPrice} text-gray-500 line-through`}>
            {formatPrice(originalPriceNum)}
          </span>
        </>
      ) : (
        <span className={`${classes.newPrice} text-gray-900`}>
          {formatPrice(priceNum > 0 ? priceNum : originalPriceNum || 0)}
        </span>
      )}
    </div>
  )
}

export default PriceTag





