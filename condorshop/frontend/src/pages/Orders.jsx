import { useState, useEffect, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import { formatPrice } from '../utils/formatPrice'
import { getProductImage } from '../utils/getProductImage'
import Spinner from '../components/common/Spinner'
import { ordersService } from '../services/orders'
import { useToast } from '../components/common/Toast'

const Orders = () => {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
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

  const loadOrders = useCallback(async () => {
    setLoading(true)
    try {
      const data = await ordersService.getUserOrders()
      setOrders(Array.isArray(data) ? data : data.results || [])
    } catch (error) {
      showToast('error', 'Error al cargar los pedidos')
      console.error('Error loading orders:', error)
    } finally {
      setLoading(false)
    }
  }, [showToast])

  useEffect(() => {
    loadOrders()
  }, [loadOrders])

  const getStatusBadge = (status) => {
    const statusColors = {
      PENDING: 'bg-yellow-100 text-yellow-800',
      CONFIRMED: 'bg-blue-100 text-blue-800',
      SHIPPED: 'bg-purple-100 text-purple-800',
      DELIVERED: 'bg-green-100 text-green-800',
      CANCELLED: 'bg-red-100 text-red-800',
    }
    
    return (
      <span
        className={`px-2 py-1 rounded-full text-xs font-semibold ${
          statusColors[status?.code] || 'bg-gray-100 text-gray-800'
        }`}
      >
        {status?.name || status?.code || 'Desconocido'}
      </span>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen flex justify-center items-center">
        <Spinner size="lg" />
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
                    {order.items?.map((item) => (
                      <div key={item.id} className="flex items-center gap-4">
                        <img
                          src={getProductImage(item.product)}
                          alt={item.product?.name}
                          className="w-16 h-16 object-cover rounded"
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
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Orders





