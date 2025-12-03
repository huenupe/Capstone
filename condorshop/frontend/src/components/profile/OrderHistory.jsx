import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useOrdersStore } from '../../store/ordersSlice'
import OrderCard from './OrderCard'
import OrderDetailsModal from './OrderDetailsModal'

// Skeleton component para mejorar percepción de fluidez
const OrderHistorySkeleton = () => (
  <div className="space-y-4">
    {[1, 2, 3].map((i) => (
      <div key={i} className="bg-gray-50 rounded-lg p-4 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-32 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-48 mb-4"></div>
        <div className="space-y-2">
          <div className="h-16 bg-gray-200 rounded"></div>
          <div className="h-16 bg-gray-200 rounded"></div>
        </div>
      </div>
    ))}
  </div>
)

const OrderHistory = () => {
  const [selectedOrder, setSelectedOrder] = useState(null)
  const [wasLoading, setWasLoading] = useState(false)
  const { orders, isLoadingOrders, errorOrders, fetchOrdersOnce } = useOrdersStore()

  // ✅ OPTIMIZACIÓN: Usar fetchOrdersOnce del store (cachea por 3 minutos)
  useEffect(() => {
    fetchOrdersOnce().catch((error) => {
      console.error('Error loading order history:', error)
      // El error ya está en el store (errorOrders)
    })
  }, [fetchOrdersOnce])

  // Detectar cuando isLoadingOrders cambia de false→true (fetch manual)
  useEffect(() => {
    if (isLoadingOrders && !wasLoading && orders.length > 0) {
      setWasLoading(true)
    } else if (!isLoadingOrders) {
      setWasLoading(false)
    }
  }, [isLoadingOrders, wasLoading, orders.length])

  // Mostrar skeletons solo cuando isLoadingOrders es true y orders.length === 0
  if (isLoadingOrders && orders.length === 0) {
    return (
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Historial de Compras</h2>
        <OrderHistorySkeleton />
      </div>
    )
  }

  if (errorOrders && orders.length === 0) {
    return (
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Historial de Compras</h2>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-800 mb-4">{errorOrders}</p>
          <button
            onClick={() => fetchOrdersOnce(true)}
            className="text-red-600 hover:text-red-800 underline text-sm"
          >
            Intentar de nuevo
          </button>
        </div>
      </div>
    )
  }

  // Mostrar máximo 10 pedidos recientes en el historial
  const displayedOrders = orders.slice(0, 10)
  const hasMoreOrders = orders.length > 10

  return (
    <>
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Historial de Compras</h2>
          {hasMoreOrders && (
            <Link to="/orders">
              <button className="text-sm text-primary-600 hover:text-primary-700 underline">
                Ver todo
              </button>
            </Link>
          )}
        </div>

        {/* Mensaje de actualización cuando se está recargando */}
        {wasLoading && orders.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 text-sm text-blue-800">
            Actualizando historial...
          </div>
        )}

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
            {displayedOrders.map((order) => (
              <OrderCard
                key={order.id}
                order={order}
                onViewDetails={() => setSelectedOrder(order)}
              />
            ))}
            {hasMoreOrders && (
              <div className="text-center pt-4">
                <Link to="/orders">
                  <button className="text-primary-600 hover:text-primary-700 underline text-sm">
                    Ver {orders.length - 10} pedido{orders.length - 10 > 1 ? 's' : ''} más →
                  </button>
                </Link>
              </div>
            )}
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

