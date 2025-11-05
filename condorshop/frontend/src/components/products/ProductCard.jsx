import { Link } from 'react-router-dom'
import PriceTag from './PriceTag'
import { getProductImage } from '../../utils/getProductImage'

const ProductCard = ({ product }) => {
  const imageUrl = getProductImage(product)
  
  const isOutOfStock = product.stock_qty === 0

  return (
    <Link
      to={`/product/${product.slug}`}
      className="block bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-shadow"
    >
      <div className="relative">
        <img
          src={imageUrl}
          alt={product.name}
          className="w-full h-48 object-cover"
          onError={(e) => {
            e.target.src = '/placeholder-product.jpg'
          }}
        />
        {isOutOfStock && (
          <div className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded text-sm font-semibold">
            Sin Stock
          </div>
        )}
        {product.stock_qty > 0 && product.stock_qty < 10 && (
          <div className="absolute top-2 right-2 bg-yellow-500 text-white px-2 py-1 rounded text-sm font-semibold">
            Pocas unidades
          </div>
        )}
      </div>
      
      <div className="p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
          {product.name}
        </h3>
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
          {product.description}
        </p>
        <PriceTag 
          price={product.final_price || product.price} 
          originalPrice={product.has_discount ? product.price : null}
          discountPercent={product.has_discount ? (product.calculated_discount_percent || product.discount_percent) : null}
          size="md"
        />
        {product.category && (
          <span className="inline-block mt-2 text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
            {product.category.name}
          </span>
        )}
      </div>
    </Link>
  )
}

export default ProductCard





