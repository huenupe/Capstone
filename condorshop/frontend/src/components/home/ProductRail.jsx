import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import Button from '../common/Button'
import Spinner from '../common/Spinner'
import PriceTag from '../products/PriceTag'
import { productsService } from '../../services/products'
import { cartService } from '../../services/cart'
import { useCartStore } from '../../store/cartSlice'
import { useToast } from '../common/Toast'
import { getProductImage } from '../../utils/getProductImage'

const ProductRail = ({ title, params = {} }) => {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const { setCart } = useCartStore()
  const toast = useToast()

  const loadProducts = useCallback(async () => {
    setLoading(true)
    try {
      const data = await productsService.getProducts({
        page_size: 10,
        ...params,
      })
      const productsList = Array.isArray(data) ? data : data.results || []
      setProducts(productsList)
    } catch (error) {
      console.error(`Error loading ${title}:`, error)
    } finally {
      setLoading(false)
    }
  }, [params, title])

  useEffect(() => {
    loadProducts()
  }, [loadProducts])

  const handleAddToCart = async (product) => {
    if (product.stock_qty === 0) {
      toast.error('Producto sin stock')
      return
    }

    try {
      await cartService.addToCart({
        product_id: product.id,
        quantity: 1,
      })

      // Refresh cart
      const cartData = await cartService.getCart()
      setCart(cartData)

      toast.success('Producto agregado al carrito')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Error al agregar al carrito')
      console.error('Error adding to cart:', error)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <Spinner size="lg" />
      </div>
    )
  }

  if (products.length === 0) {
    // No mostrar nada si no hay productos (no es error)
    return null
  }

  return (
    <div className="mb-12">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
        <Link to="/">
          <Button variant="outline" size="sm">
            Ver todos
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {products.map((product) => (
          <div
            key={product.id}
            className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-shadow"
          >
            <Link to={`/product/${product.slug}`} className="block">
              <div className="relative">
                <img
                  src={getProductImage(product)}
                  alt={product.name}
                  className="w-full h-48 object-cover"
                  onError={(e) => {
                    e.target.src = '/placeholder-product.jpg'
                  }}
                />
                {product.stock_qty === 0 && (
                  <div className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded text-xs font-semibold">
                    Sin Stock
                  </div>
                )}
              </div>

              <div className="p-4">
                <h3 className="text-sm font-semibold text-gray-900 mb-2 line-clamp-2 min-h-[2.5rem]">
                  {product.name}
                </h3>
                <PriceTag
                  price={product.final_price || product.price}
                  originalPrice={product.has_discount ? product.price : null}
                  discountPercent={product.has_discount ? (product.calculated_discount_percent || product.discount_percent) : null}
                  size="sm"
                />
              </div>
            </Link>
            <div className="px-4 pb-4">
              <Button
                onClick={() => handleAddToCart(product)}
                disabled={product.stock_qty === 0}
                fullWidth
                size="sm"
                className="focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {product.stock_qty === 0 ? 'Sin Stock' : 'Agregar al carrito'}
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default ProductRail

