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
  const [updating, setUpdating] = useState(null)
  const [localQuantities, setLocalQuantities] = useState({})
  const {
    items,
    subtotal,
    total,
    totalDiscount,
    isLoading,
    fetchCart,
    updateItemQuantity,
    updateItemFromBackend,
    removeItem,
  } = useCartStore()
  const { isAuthenticated } = useAuthStore()
  const toast = useToast()
  const toastRef = useRef(toast)
  
  // Protección contra React.StrictMode (doble ejecución en desarrollo)
  const hasFetchedRef = useRef(false)
  const lastAuthStateRef = useRef(isAuthenticated)
  const debounceTimersRef = useRef({})

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

  // ✅ OPTIMIZACIÓN: Un solo useEffect que maneja carga inicial y cambios de autenticación
  // Protegido contra StrictMode con useRef
  // ✅ MEJORA: Funciona tanto para usuarios autenticados como invitados (guests)
  useEffect(() => {
    // Si ya se hizo fetch y el estado de autenticación no cambió, no hacer nada
    if (hasFetchedRef.current && lastAuthStateRef.current === isAuthenticated) {
      return
    }
    
    hasFetchedRef.current = true
    lastAuthStateRef.current = isAuthenticated
    
    // Fetch del carrito (funciona para autenticados y guests)
    // La lógica de guest vs authenticated está en el backend
    fetchCart().catch((error) => {
      console.error('Error loading cart:', error)
      // No mostrar error si es 401/403 para guests (es normal si no hay session_token aún)
      const accessToken = localStorage.getItem('accessToken')
      if (accessToken && error.response?.status !== 401 && error.response?.status !== 403) {
        showToast('error', 'Error al cargar el carrito')
      }
    })
  }, [isAuthenticated, fetchCart, showToast])

  // Inicializar localQuantities cuando cambian los items
  useEffect(() => {
    const initialQuantities = {}
    items.forEach(item => {
      if (item.id) {
        initialQuantities[item.id] = item.quantity
      }
    })
    setLocalQuantities(prev => {
      // Solo actualizar si hay cambios reales (evitar loops)
      const hasChanges = items.some(item => item.id && prev[item.id] !== item.quantity)
      if (hasChanges || Object.keys(prev).length !== Object.keys(initialQuantities).length) {
        return initialQuantities
      }
      return prev
    })
  }, [items]) // Actualizar cuando cambian los items

  // Cleanup de timers al desmontar
  useEffect(() => {
    return () => {
      Object.values(debounceTimersRef.current).forEach(timer => {
        if (timer) clearTimeout(timer)
      })
    }
  }, [])

  // Flag para mostrar toast solo la primera vez
  const hasShownSavingToastRef = useRef({})

  // ✅ MEJORA: Calcular totales optimistas inmediatamente
  const calculateOptimisticTotals = useCallback((items, localQty) => {
    if (!Array.isArray(items) || items.length === 0) {
      return { subtotal: 0, total: 0, totalDiscount: 0, shipping: 0 }
    }

    const subtotal = items.reduce((sum, item) => {
      const qty = localQty[item.id] ?? item.quantity
      const price = parseFloat(item.unit_price) || 0
      return sum + (price * qty)
    }, 0)

    const totalDiscount = items.reduce((sum, item) => {
      const qty = localQty[item.id] ?? item.quantity
      const originalPrice = parseFloat(item.product?.price || item.unit_price) || 0
      const discountedPrice = parseFloat(item.unit_price) || 0
      if (originalPrice > discountedPrice) {
        return sum + ((originalPrice - discountedPrice) * qty)
      }
      return sum
    }, 0)

    const FREE_SHIPPING_THRESHOLD = 50000
    const SHIPPING_COST = 5000
    const shipping = subtotal >= FREE_SHIPPING_THRESHOLD ? 0 : SHIPPING_COST
    const total = subtotal + shipping

    return { subtotal, total, totalDiscount, shipping }
  }, [])

  // Estado para totales optimistas
  const [optimisticTotals, setOptimisticTotals] = useState(null)

  // Calcular totales optimistas cuando cambian items o localQuantities
  useEffect(() => {
    if (items.length > 0) {
      const totals = calculateOptimisticTotals(items, localQuantities)
      setOptimisticTotals(totals)
    } else {
      setOptimisticTotals(null)
    }
  }, [items, localQuantities, calculateOptimisticTotals])

  // Handler inmediato para actualizar UI (optimistic)
  const handleQuantityChange = (itemId, newQuantity) => {
    if (newQuantity < 1) {
      handleRemoveItem(itemId)
      return
    }

    // ✅ OPTIMISTIC UI: Actualizar UI inmediatamente
    setLocalQuantities(prev => {
      const updated = { ...prev, [itemId]: newQuantity }
      // ✅ MEJORA: Calcular totales optimistas INMEDIATAMENTE
      const totals = calculateOptimisticTotals(items, updated)
      setOptimisticTotals(totals)
      return updated
    })
    updateItemQuantity(itemId, newQuantity)

    // ✅ TOAST SUAVE: Mostrar "Guardando cambios..." solo la primera vez por item
    if (!hasShownSavingToastRef.current[itemId]) {
      hasShownSavingToastRef.current[itemId] = true
      // Toast discreto y no intrusivo
      if (import.meta.env.DEV) {
        console.log('[Cart] Guardando cambios para item', itemId)
      }
    }

    // Limpiar timer anterior si existe
    if (debounceTimersRef.current[itemId]) {
      clearTimeout(debounceTimersRef.current[itemId])
    }

    // ✅ DEBOUNCE: Esperar 250ms antes de enviar al backend
    debounceTimersRef.current[itemId] = setTimeout(() => {
      handleUpdateQuantityDebounced(itemId, newQuantity)
    }, 250)
  }

  // Handler que se ejecuta después del debounce
  const handleUpdateQuantityDebounced = async (itemId, quantity) => {
    // Prevenir múltiples peticiones simultáneas para el mismo item
    if (updating === itemId) {
      return
    }

    // Guardar cantidad anterior para revertir en caso de error
    const previousQuantity = localQuantities[itemId]

    setUpdating(itemId)

    try {
      // ✅ Sincronizar con servidor - usar respuesta del backend para actualizar item específico
      const response = await cartService.updateCartItem(itemId, { quantity })
      
      // ✅ OPTIMIZACIÓN: Actualizar solo el item específico con la respuesta del backend
      // El backend devuelve: { message: 'Item actualizado', item: { ... } }
      // No recargar todo el carrito
      if (response && response.item) {
        // El backend devuelve el item en response.item
        updateItemFromBackend(response.item)
        // ✅ MEJORA: Recalcular totales con datos del backend
        const { items: updatedItems } = useCartStore.getState()
        const totals = calculateOptimisticTotals(updatedItems, localQuantities)
        setOptimisticTotals(totals)
      } else if (response && response.id) {
        // Fallback: si la respuesta es el item directamente
        updateItemFromBackend(response)
        const { items: updatedItems } = useCartStore.getState()
        const totals = calculateOptimisticTotals(updatedItems, localQuantities)
        setOptimisticTotals(totals)
      }
      
      // No mostrar toast para cada cambio (evitar spam)
    } catch (error) {
      // Revertir cambio en caso de error
      if (previousQuantity !== undefined) {
        setLocalQuantities(prev => {
          const reverted = { ...prev, [itemId]: previousQuantity }
          // Recalcular totales con valores revertidos
          const { items: currentItems } = useCartStore.getState()
          const totals = calculateOptimisticTotals(currentItems, reverted)
          setOptimisticTotals(totals)
          return reverted
        })
        updateItemQuantity(itemId, previousQuantity)
      }
      showToast('error', error.response?.data?.error || 'Error al actualizar cantidad')
      console.error('Error updating cart item:', error)
    } finally {
      setUpdating(null)
      delete debounceTimersRef.current[itemId]
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
    
    // Limpiar debounce timer si existe
    if (debounceTimersRef.current[itemId]) {
      clearTimeout(debounceTimersRef.current[itemId])
      delete debounceTimersRef.current[itemId]
    }
    
    // ✅ OPTIMISTIC UI: Eliminar inmediatamente de la UI para respuesta instantánea
    setUpdating(itemId)
    removeItem(itemId)
    
    // Actualizar localQuantities
    setLocalQuantities(prev => {
      const newQuantities = { ...prev }
      delete newQuantities[itemId]
      return newQuantities
    })

    try {
      // Sincronizar con servidor en background
      await cartService.removeCartItem(itemId)
      // Si la petición fue exitosa, no necesitamos hacer nada más
      // El item ya fue eliminado del estado local
    } catch (error) {
      // ✅ MEJORA: Manejar 404 correctamente (producto ya no existe)
      if (error.response?.status === 404) {
        // El item ya no existe en el backend, mantener el estado actual
        // No mostrar error ya que la operación fue exitosa (optimistic delete funcionó)
        if (import.meta.env.DEV) {
          console.log('[Cart] Item ya no existe en backend (404), manteniendo estado optimista')
        }
      } else if (error.response?.status === 200) {
        // Backend confirmó eliminación exitosa
        // No hacer nada, el estado ya está actualizado
      } else {
        // Otro tipo de error - revertir cambio insertando el item de nuevo
        if (itemToRemove) {
          const { items: currentItems, setCart } = useCartStore.getState()
          const newItems = [...currentItems, itemToRemove]
          // Usar setCart para actualizar correctamente con cálculo de totales
          setCart({ items: newItems })
          
          setLocalQuantities(prev => ({ ...prev, [itemId]: itemToRemove.quantity }))
        }
        showToast('error', 'Error al eliminar producto')
        console.error('Error removing cart item:', error)
      }
    } finally {
      setUpdating(null)
    }
  }

  if (isLoading) {
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
                        value={localQuantities[item.id] ?? item.quantity}
                        onChange={(qty) => handleQuantityChange(item.id, qty)}
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
                  <span>{formatPrice(optimisticTotals?.subtotal ?? subtotal ?? 0)}</span>
                </div>
                {(optimisticTotals?.totalDiscount ?? totalDiscount) > 0 && (
                  <div className="flex justify-between text-gray-700">
                    <span className="text-green-600">Descuentos</span>
                    <span className="text-green-600 font-semibold">-{formatPrice(optimisticTotals?.totalDiscount ?? totalDiscount ?? 0)}</span>
                  </div>
                )}
                
                <div className="border-t pt-3 flex justify-between text-xl font-bold text-gray-900">
                  <span>Total</span>
                  <span>{formatPrice(optimisticTotals?.total ?? total ?? subtotal ?? 0)}</span>
                </div>
              </div>

              <Button
                onClick={() => {
                  // ✅ CORRECCIÓN: Permitir checkout para invitados
                  // Autenticados: Carro → Dirección → Pago (3 pasos)
                  // Invitados: Carro → Datos → Dirección → Pago (4 pasos)
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





