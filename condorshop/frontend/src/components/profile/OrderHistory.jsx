import { useState, useEffect, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import { ordersService } from '../../services/orders'
import { useToast } from '../common/Toast'
import Spinner from '../common/Spinner'
import OrderCard from './OrderCard'
import OrderDetailsModal from './OrderDetailsModal'

const OrderHistory = () => {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedOrder, setSelectedOrder] = useState(null)
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
    setError(null)
    try {
      const data = await ordersService.getUserOrders()
      setOrders(Array.isArray(data) ? data : data.results || [])
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Error al cargar el historial de compras'
      setError(errorMessage)
      showToast('error', errorMessage)
      console.error('Error loading order history:', err)
    } finally {
      setLoading(false)
    }
  }, [showToast])

  useEffect(() => {
    loadOrders()
  }, [loadOrders])

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner size="lg" />
      </div>
    )
  }

  if (error && orders.length === 0) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <p className="text-red-800 mb-4">{error}</p>
        <button
          onClick={loadOrders}
          className="text-red-600 hover:text-red-800 underline text-sm"
        >
          Intentar de nuevo
        </button>
      </div>
    )
  }

  return (
    <>
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Historial de Compras</h2>

        {orders.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg">
            <div className="text-6xl mb-4">📦</div>
            <p className="text-gray-600 mb-4 text-lg">
              No tienes compras realizadas aún
            </p>
            <Link to="/">
              <button className="inline-block bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 transition-colors">
                Comenzar a comprar →
              </button>
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {orders.map((order) => (
              <OrderCard
                key={order.id}
                order={order}
                onViewDetails={() => setSelectedOrder(order)}
              />
            ))}
          </div>
        )}
      </div>

      {selectedOrder && (
        <OrderDetailsModal
          order={selectedOrder}
          onClose={() => setSelectedOrder(null)}
        />
      )}
    </>
  )
}

export default OrderHistory

