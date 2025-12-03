import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { formatPrice } from '../utils/formatPrice'
import { getProductImage } from '../utils/getProductImage'
import Spinner from '../components/common/Spinner'
import Button from '../components/common/Button'
import OptimizedImage from '../components/common/OptimizedImage'
import { ordersService } from '../services/orders'
import paymentsService from '../services/paymentsService'
import { useOrdersStore } from '../store/ordersSlice'
import { useToast } from '../components/common/Toast'

// Skeleton component para mejorar percepción de fluidez
const OrderSkeleton = () => (
  <div className="bg-white rounded-lg shadow-md p-6 animate-pulse">
    <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-4">
      <div className="flex-1">
        <div className="h-6 bg-gray-200 rounded w-32 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-48"></div>
      </div>
      <div className="h-6 bg-gray-200 rounded w-20 mt-2 md:mt-0"></div>
    </div>
    <div className="border-t pt-4">
      <div className="space-y-2 mb-4">
        {[1, 2].map((i) => (
          <div key={i} className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gray-200 rounded"></div>
            <div className="flex-1">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
            <div className="h-4 bg-gray-200 rounded w-20"></div>
          </div>
        ))}
      </div>
      <div className="flex justify-between items-center border-t pt-4">
        <div className="h-4 bg-gray-200 rounded w-24"></div>
        <div className="h-6 bg-gray-200 rounded w-32"></div>
      </div>
    </div>
  </div>
)

const Orders = () => {
  const [processingOrderId, setProcessingOrderId] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [retryCount, setRetryCount] = useState(0)
  const { orders, pagination, isLoadingOrders, errorOrders, fetchOrdersOnce, prefetchedNextPage } = useOrdersStore()
  const toast = useToast()
  const toastRef = useRef(toast)

  useEffect(() => {
    toastRef.current = toast
  }, [toast])

  // ✅ OPTIMIZACIÓN: Usar fetchOrdersOnce del store (cachea por 3 minutos)
  // Si ya hay datos frescos en memoria, no hace request duplicado
  // ✅ PAGINACIÓN: Cargar página específica
  useEffect(() => {
    fetchOrdersOnce(false, { page: currentPage, page_size: 20 }).catch((error) => {
      console.error('Error loading orders:', error)
      // El error ya está en el store (errorOrders)
      setRetryCount(prev => prev + 1)
      if (toastRef.current) {
        toastRef.current.error('Error al cargar los pedidos')
      }
    })
  }, [fetchOrdersOnce, currentPage])

  // ✅ PREFETCH: Cargar siguiente página cuando el usuario está cerca del final
  useEffect(() => {
    if (pagination.next && !isLoadingOrders) {
      // Prefetch cuando hay siguiente página disponible
      const { prefetchNextPage } = useOrdersStore.getState()
      prefetchNextPage(pagination.next).catch(() => {
        // Silencioso, no crítico
      })
    }
  }, [pagination.next, isLoadingOrders])

  // Mostrar toast si hay error (solo una vez)
  useEffect(() => {
    if (errorOrders && toastRef.current && retryCount <= 1) {
      toastRef.current.error(errorOrders)
    }
  }, [errorOrders, retryCount])

  const getStatusBadge = (status) => {
    // Mapeo de colores por código de estado (el label viene del backend en español)
    const statusColors = {
      PENDING: 'bg-yellow-100 text-yellow-800',
      PAID: 'bg-blue-100 text-blue-800',
      FAILED: 'bg-red-100 text-red-800',
      CANCELLED: 'bg-red-100 text-red-800',
      PREPARING: 'bg-orange-100 text-orange-800',
      SHIPPED: 'bg-purple-100 text-purple-800',
      DELIVERED: 'bg-green-100 text-green-800',
    }
    
    // Usar la descripción del backend (ya viene en español)
    const label = status?.description || status?.code || 'Desconocido'
    
    return (
      <span
        className={`px-2 py-1 rounded-full text-xs font-semibold ${
          statusColors[status?.code] || 'bg-gray-100 text-gray-800'
        }`}
      >
        {label}
      </span>
    )
  }

  const handleRetryPayment = async (orderId) => {
    setProcessingOrderId(orderId)
    try {
      const webpayEnabled = import.meta.env.VITE_WEBPAY_ENABLED === 'true'
      
      if (!webpayEnabled) {
        if (toastRef.current) {
          toastRef.current.error('Webpay no está habilitado')
        }
        setProcessingOrderId(null)
        return
      }

      const paymentResponse = await paymentsService.initiateWebpayPayment(orderId)
      
      if (paymentResponse.success && paymentResponse.token && paymentResponse.url) {
        // Guardar order_id en sessionStorage
        sessionStorage.setItem('pending_order_id', orderId)
        sessionStorage.setItem('pending_order_amount', paymentResponse.amount || 0)
        
        if (toastRef.current) {
          toastRef.current.success('Redirigiendo a Webpay...')
        }
        
        // Pequeño delay para que el usuario vea el mensaje
        setTimeout(() => {
          paymentsService.redirectToWebpay(paymentResponse.token, paymentResponse.url)
        }, 1000)
        
        // ✅ OPTIMIZACIÓN: Recargar órdenes después de iniciar pago (force=true)
        await fetchOrdersOnce(true)
        if (toastRef.current) {
          toastRef.current.success('Datos actualizados')
        }
      } else {
        throw new Error('Respuesta inválida de Webpay')
      }
    } catch (error) {
      console.error('Error al reintentar pago:', error)
      if (toastRef.current) {
        toastRef.current.error(error.response?.data?.error || 'Error al iniciar el pago')
      }
      setProcessingOrderId(null)
    }
  }

  const handleCancelOrder = async (orderId) => {
    if (!window.confirm('¿Estás seguro de que deseas cancelar este pedido?')) {
      return
    }

    setProcessingOrderId(orderId)
    try {
      await ordersService.cancelOrder(orderId)
      if (toastRef.current) {
        toastRef.current.success('Pedido cancelado exitosamente')
      }
      // ✅ OPTIMIZACIÓN: Recargar usando fetchOrdersOnce con force=true para refrescar datos
      await fetchOrdersOnce(true)
      if (toastRef.current) {
        toastRef.current.success('Datos actualizados')
      }
    } catch (error) {
      console.error('Error al cancelar pedido:', error)
      if (toastRef.current) {
        toastRef.current.error(error.response?.data?.error || 'Error al cancelar el pedido')
      }
    } finally {
      setProcessingOrderId(null)
    }
  }

  // Mostrar skeletons solo cuando isLoadingOrders es true y orders.length === 0
  if (isLoadingOrders && orders.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Mis Pedidos</h1>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <OrderSkeleton key={i} />
            ))}
          </div>
        </div>
      </div>
    )
  }

  // ✅ MEJORA: Mostrar error persistente si hay más de 2 intentos fallidos
  if (errorOrders && retryCount > 2 && orders.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Mis Pedidos</h1>
          <div className="bg-red-50 border border-red-200 rounded-lg p-8 text-center">
            <p className="text-red-800 mb-4 text-lg">{errorOrders}</p>
            <p className="text-red-600 mb-6 text-sm">No se pudo cargar después de varios intentos.</p>
            <Button
              onClick={() => {
                setRetryCount(0)
                fetchOrdersOnce(true).catch(() => {})
              }}
            >
              Reintentar
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Mis Pedidos</h1>

        {orders.length === 0 ? (
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
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">No tienes pedidos aún</h2>
            <p className="text-gray-600 mb-6">Cuando realices tu primer pedido, aparecerá aquí</p>
            <Link to="/">
              <button className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 transition-colors">
                Ir a Comprar
              </button>
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {orders.map((order) => (
              <div key={order.id} className="bg-white rounded-lg shadow-md p-6">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      Pedido #{order.order_number || order.id}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {new Date(order.created_at).toLocaleDateString('es-CL', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                  <div className="mt-2 md:mt-0">
                    {getStatusBadge(order.status)}
                  </div>
                </div>

                <div className="border-t pt-4">
                  <div className="space-y-2 mb-4">
                    {order.items?.map((item, itemIndex) => (
                      <div key={item.id} className="flex items-center gap-4">
                        <OptimizedImage
                          src={getProductImage(item.product)}
                          alt={item.product?.name}
                          className="w-16 h-16 object-cover rounded"
                          width={64}
                          height={64}
                          loading={itemIndex < 2 ? 'eager' : 'lazy'}
                          onError={(e) => {
                            e.target.src = '/placeholder-product.jpg'
                          }}
                        />
                        <div className="flex-1">
                          <Link
                            to={`/product/${item.product?.slug}`}
                            className="text-gray-900 hover:text-primary-600 font-medium"
                          >
                            {item.product?.name}
                          </Link>
                          <p className="text-sm text-gray-600">
                            Cantidad: {item.quantity} x {formatPrice(item.unit_price)}
                          </p>
                        </div>
                        <p className="font-semibold text-gray-900">
                          {formatPrice(item.total_price)}
                        </p>
                      </div>
                    ))}
                  </div>

                  <div className="flex justify-between items-center border-t pt-4">
                    <div className="text-sm text-gray-600">
                      <p>
                        <span className="font-medium">Envío:</span>{' '}
                        {order.shipping_cost === 0 ? 'GRATIS' : formatPrice(order.shipping_cost)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-600">Total</p>
                      <p className="text-xl font-bold text-gray-900">
                        {formatPrice(order.total_amount)}
                      </p>
                    </div>
                  </div>

                  {/* Botones de acción para pedidos PENDING */}
                  {order.status?.code === 'PENDING' && (
                    <div className="flex gap-3 mt-4 pt-4 border-t">
                      <Button
                        onClick={() => handleRetryPayment(order.id)}
                        disabled={processingOrderId === order.id}
                        className="flex-1"
                      >
                        {processingOrderId === order.id ? (
                          <>
                            <Spinner size="sm" className="mr-2" />
                            Procesando...
                          </>
                        ) : (
                          'Pagar Ahora'
                        )}
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => handleCancelOrder(order.id)}
                        disabled={processingOrderId === order.id}
                        className="flex-1"
                      >
                        Cancelar Pedido
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ✅ PAGINACIÓN: Controles de paginación */}
        {pagination && pagination.count > 0 && (
          <div className="mt-8 flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Mostrando {((currentPage - 1) * (pagination.pageSize || 20)) + 1} - {Math.min(currentPage * (pagination.pageSize || 20), pagination.count)} de {pagination.count} pedidos
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={!pagination.previous || isLoadingOrders}
              >
                Anterior
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => prev + 1)}
                disabled={!pagination.next || isLoadingOrders}
              >
                Siguiente
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Orders





