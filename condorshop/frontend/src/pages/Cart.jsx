import { useState, useEffect, useCallback, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { formatPrice } from '../utils/formatPrice'
import { getProductImage } from '../utils/getProductImage'
import QuantityStepper from '../components/forms/QuantityStepper'
import Button from '../components/common/Button'
import Spinner from '../components/common/Spinner'
import PriceTag from '../components/products/PriceTag'
import OptimizedImage from '../components/common/OptimizedImage'
import { cartService } from '../services/cart'
import { useCartStore } from '../store/cartSlice'
import { useAuthStore } from '../store/authSlice'
import { useToast } from '../components/common/Toast'

const Cart = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(null)
  const {
    items,
    subtotal,
    total,
    totalDiscount,
    setCart,
    updateItemQuantity,
    removeItem,
    updateTotals,
  } = useCartStore()
  const { isAuthenticated } = useAuthStore()
  const toast = useToast()
  const toastRef = useRef(toast)

  useEffect(() => {
    toastRef.current = toast
  }, [toast])

  const showToast = useCallback((type, message) => {
    const current = toastRef.current
    if (!current || typeof current[type] !== 'function') {
      return
    }
    current[type](message)
  }, [])

  const loadCart = useCallback(async () => {
    setLoading(true)
    try {
      const data = await cartService.getCart()
      setCart(data)
    } catch (error) {
      console.error('Error loading cart:', error)
      showToast('error', 'Error al cargar el carrito')
    } finally {
      setLoading(false)
    }
  }, [setCart, showToast])

  useEffect(() => {
    loadCart()
  }, [loadCart])

  const handleUpdateQuantity = async (itemId, quantity) => {
    if (quantity < 1) {
      handleRemoveItem(itemId)
      return
    }

    // Guardar cantidad anterior para revertir en caso de error
    const previousItem = items.find(item => item.id === itemId)
    const previousQuantity = previousItem?.quantity

    // Optimistic update: actualizar UI inmediatamente
    setUpdating(itemId)
    updateItemQuantity(itemId, quantity)
    updateTotals()
    
    // Mostrar toast inmediatamente
    showToast('success', 'Cantidad actualizada')

    try {
      // Sincronizar con servidor en background
      await cartService.updateCartItem(itemId, { quantity })
    } catch (error) {
      // Revertir cambio en caso de error
      if (previousQuantity) {
        updateItemQuantity(itemId, previousQuantity)
        updateTotals()
      }
      showToast('error', error.response?.data?.error || 'Error al actualizar cantidad')
      console.error('Error updating cart item:', error)
      // Recargar carrito para sincronizar con servidor
      await loadCart()
    } finally {
      setUpdating(null)
    }
  }

  const handleRemoveItem = async (itemId) => {
    // Prevenir múltiples peticiones simultáneas para el mismo item
    if (updating === itemId) {
      return
    }
    
    // Guardar item para revertir en caso de error
    const itemToRemove = items.find(item => item.id === itemId)
    if (!itemToRemove) {
      // Item ya no existe, no hacer nada
      return
    }
    
    // Optimistic update: eliminar inmediatamente de la UI
    setUpdating(itemId)
    removeItem(itemId)
    updateTotals()
    
    // Mostrar toast inmediatamente
    showToast('success', 'Producto eliminado del carrito')

    try {
      // Sincronizar con servidor en background
      await cartService.removeCartItem(itemId)
      // Si la petición fue exitosa (200 o 204), no necesitamos hacer nada más
      // El item ya fue eliminado del estado local
    } catch (error) {
      // Si el error es 404, el item ya no existe en el backend
      // El backend ahora devuelve 200 si ya no existe, pero por compatibilidad
      // manejamos también 404
      if (error.response?.status === 404 || error.response?.status === 200) {
        // El item ya no existe en el backend, mantener el estado actual
        // No mostrar error ya que la operación fue exitosa
      } else {
        // Otro tipo de error - revertir cambio recargando carrito completo
        if (itemToRemove) {
          await loadCart()
        }
        showToast('error', 'Error al eliminar producto')
        console.error('Error removing cart item:', error)
      }
    } finally {
      setUpdating(null)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex justify-center items-center">
        <Spinner size="lg" />
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <svg
              className="mx-auto h-24 w-24 text-gray-400 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Tu carrito está vacío</h2>
            <p className="text-gray-600 mb-6">Agrega algunos productos para comenzar</p>
            <Link to="/">
              <Button>Ir a Comprar</Button>
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Carrito de Compras</h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Items */}
          <div className="lg:col-span-2 space-y-4">
            {items.map((item, index) => (
              <div key={item.id} className="bg-white rounded-lg shadow-md p-6">
                <div className="flex gap-4">
                  <OptimizedImage
                    src={getProductImage(item.product)}
                    alt={item.product?.name || 'Producto'}
                    className="w-24 h-24 object-cover rounded flex-shrink-0"
                    width={96}
                    height={96}
                    priority={index === 0} // Primera imagen con prioridad alta (LCP)
                    onError={(e) => {
                      e.target.src = '/placeholder-product.jpg'
                    }}
                  />
                  
                  <div className="flex-1">
                    <Link to={`/product/${item.product?.slug}`}>
                      <h3 className="text-lg font-semibold text-gray-900 hover:text-primary-600">
                        {item.product?.name}
                      </h3>
                    </Link>
                    <div className="mb-2">
                      <PriceTag
                        price={parseFloat(item.unit_price) || parseFloat(item.product?.final_price) || parseFloat(item.product?.price)}
                        originalPrice={item.product?.has_discount ? parseFloat(item.product.price) : null}
                        discountPercent={item.product?.has_discount ? (item.product.calculated_discount_percent || item.product.discount_percent) : null}
                        size="sm"
                      />
                    </div>
                    
                    <div className="flex items-center gap-4 mt-4">
                      <QuantityStepper
                        value={item.quantity}
                        onChange={(qty) => handleUpdateQuantity(item.id, qty)}
                        disabled={updating === item.id}
                        max={item.product?.stock_qty || 999}
                      />
                      
                      <div className="flex-1 text-right">
                        <p className="text-lg font-semibold text-gray-900">
                          {formatPrice(item.unit_price * item.quantity)}
                        </p>
                      </div>
                      
                      <button
                        onClick={() => handleRemoveItem(item.id)}
                        disabled={updating === item.id}
                        className="text-red-600 hover:text-red-700 disabled:opacity-50"
                        title="Eliminar"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Summary */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-6 sticky top-4">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Resumen de la compra</h2>
              
              <div className="space-y-3 mb-4">
                <div className="flex justify-between text-gray-700">
                  <span>Productos ({items.length})</span>
                  <span>{formatPrice(subtotal || 0)}</span>
                </div>
                {totalDiscount > 0 && (
                  <div className="flex justify-between text-gray-700">
                    <span className="text-green-600">Descuentos</span>
                    <span className="text-green-600 font-semibold">-{formatPrice(totalDiscount || 0)}</span>
                  </div>
                )}
                
                <div className="border-t pt-3 flex justify-between text-xl font-bold text-gray-900">
                  <span>Total</span>
                  <span>{formatPrice(total ?? subtotal ?? 0)}</span>
                </div>
              </div>

              <Button
                onClick={() => {
                  // Para usuarios autenticados, ir directo a dirección
                  // Para invitados, ir a datos del cliente primero
                  if (isAuthenticated) {
                    navigate('/checkout/address')
                  } else {
                    navigate('/checkout/customer')
                  }
                }}
                fullWidth
                size="lg"
              >
                Continuar compra
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Cart





