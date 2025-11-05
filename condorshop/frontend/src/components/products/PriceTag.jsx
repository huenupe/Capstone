import { formatPrice } from '../../utils/formatPrice'

const PriceTag = ({ price, originalPrice, className = '' }) => {
  const hasDiscount = originalPrice && originalPrice > price

  return (
    <div className={`${className}`}>
      <div className="flex items-center gap-2">
        <span className="text-2xl font-bold text-gray-900">{formatPrice(price)}</span>
        {hasDiscount && (
          <>
            <span className="text-lg text-gray-500 line-through">
              {formatPrice(originalPrice)}
            </span>
            <span className="text-sm font-semibold text-red-600 bg-red-100 px-2 py-0.5 rounded">
              {Math.round(((originalPrice - price) / originalPrice) * 100)}% OFF
            </span>
          </>
        )}
      </div>
    </div>
  )
}

export default PriceTag





