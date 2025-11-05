import { formatPrice } from '../../utils/formatPrice'

const PriceTag = ({ 
  price, 
  originalPrice, 
  discountPercent,
  className = '',
  size = 'lg' // 'sm' | 'md' | 'lg'
}) => {
  const hasDiscount = originalPrice && originalPrice > price
  const discount = discountPercent || (hasDiscount ? Math.round(((originalPrice - price) / originalPrice) * 100) : 0)

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
      {hasDiscount ? (
        <>
          {/* Precio nuevo arriba con badge de descuento */}
          <div className="flex items-center gap-2 mb-1">
            <span className={`${classes.newPrice} text-red-600`}>
              {formatPrice(price)}
            </span>
            <span className={`${classes.badge} font-semibold text-white bg-red-600 rounded`}>
              -{discount}%
            </span>
          </div>
          {/* Precio antiguo tachado abajo */}
          <span className={`${classes.oldPrice} text-gray-500 line-through`}>
            {formatPrice(originalPrice)}
          </span>
        </>
      ) : (
        <span className={`${classes.newPrice} text-gray-900`}>
          {formatPrice(price)}
        </span>
      )}
    </div>
  )
}

export default PriceTag





