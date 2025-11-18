import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ProductGallery from '../components/products/ProductGallery'
import PriceTag from '../components/products/PriceTag'
import QuantityStepper from '../components/forms/QuantityStepper'
import Button from '../components/common/Button'
import Spinner from '../components/common/Spinner'
import { productsService } from '../services/products'
import { cartService } from '../services/cart'
import { useCartStore } from '../store/cartSlice'
import { useToast } from '../components/common/Toast'

const ProductDetail = () => {
  const { slug } = useParams()
  const navigate = useNavigate()
  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(true)
  const [quantity, setQuantity] = useState(1)
  const [addingToCart, setAddingToCart] = useState(false)
  const { setCart } = useCartStore()
  const toast = useToast()
  const toastRef = useRef(toast)

  const loadProduct = useCallback(async () => {
    setLoading(true)
    try {
      const data = await productsService.getProductBySlug(slug)
      setProduct(data)
    } catch (error) {
      toastRef.current?.error?.('Error al cargar el producto')
      console.error('Error loading product:', error)
      navigate('/')
    } finally {
      setLoading(false)
    }
  }, [navigate, slug])

  useEffect(() => {
    loadProduct()
  }, [loadProduct])

  useEffect(() => {
    toastRef.current = toast
  }, [toast])

  const handleAddToCart = async () => {
    if (!product || product.stock_qty === 0) return

    setAddingToCart(true)
    
    // Mostrar toast inmediatamente (optimistic UI)
    toast.success('Producto agregado al carrito')
    
    try {
      await cartService.addToCart({
        product_id: product.id,
        quantity,
      })

      // Refresh cart en background (sin bloquear UI)
      cartService.getCart().then(cartData => {
        setCart(cartData)
      }).catch(err => {
        console.error('Error refreshing cart:', err)
      })
    } catch (error) {
      // Si falla, mostrar error y recargar carrito para sincronizar
      toast.error(error.response?.data?.error || 'Error al agregar al carrito')
      console.error('Error adding to cart:', error)
      cartService.getCart().then(cartData => {
        setCart(cartData)
      }).catch(err => {
        console.error('Error refreshing cart after error:', err)
      })
    } finally {
      setAddingToCart(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex justify-center items-center">
        <Spinner size="lg" />
      </div>
    )
  }

  if (!product) {
    return (
      <div className="min-h-screen flex justify-center items-center">
        <div className="text-center">
          <p className="text-gray-500 text-lg mb-4">Producto no encontrado</p>
          <Button onClick={() => navigate('/')}>Volver al inicio</Button>
        </div>
      </div>
    )
  }

  const isOutOfStock = product.stock_qty === 0
  const maxQuantity = Math.min(product.stock_qty, 999)

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 p-8">
            {/* Images */}
            <div>
              <ProductGallery images={product.images || []} productName={product.name} />
            </div>

            {/* Info */}
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-4">{product.name}</h1>
              
              {product.category && (
                <span className="inline-block mb-4 text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded">
                  {product.category.name}
                </span>
              )}

              <PriceTag 
                price={product.final_price || product.price} 
                originalPrice={product.has_discount ? product.price : null}
                discountPercent={product.has_discount ? (product.calculated_discount_percent || product.discount_percent) : null}
                size="lg"
                className="mb-6" 
              />

              {product.description && (
                <div className="mb-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-2">Descripción</h2>
                  <p className="text-gray-700 whitespace-pre-line">{product.description}</p>
                </div>
              )}

              <div className="mb-6">
                <p className="text-sm text-gray-600 mb-2">
                  <span className="font-semibold">Stock disponible:</span>{' '}
                  {isOutOfStock ? (
                    <span className="text-red-600 font-semibold">Sin stock</span>
                  ) : (
                    <span className={product.stock_qty < 10 ? 'text-yellow-600' : 'text-green-600'}>
                      {product.stock_qty} unidades
                    </span>
                  )}
                </p>
              </div>

              <div className="border-t pt-6">
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Cantidad
                  </label>
                  <QuantityStepper
                    value={quantity}
                    onChange={setQuantity}
                    min={1}
                    max={maxQuantity}
                    disabled={isOutOfStock}
                  />
                </div>

                <Button
                  onClick={handleAddToCart}
                  disabled={isOutOfStock || addingToCart}
                  fullWidth
                  size="lg"
                >
                  {addingToCart ? 'Agregando...' : isOutOfStock ? 'Sin Stock' : 'Agregar al Carrito'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ProductDetail





