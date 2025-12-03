import { Link } from 'react-router-dom'
import { formatPrice } from '../../utils/formatPrice'
import { getProductImage } from '../../utils/getProductImage'
import OptimizedImage from '../common/OptimizedImage'
import Button from '../common/Button'

const OrderCard = ({ order, onViewDetails }) => {
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
    const color = statusColors[status?.code] || 'bg-gray-100 text-gray-800'
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${color}`}>
        {label}
      </span>
    )
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('es-CL', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  }

  // Mostrar solo los primeros 3 items en la vista resumida
  const displayedItems = order.items?.slice(0, 3) || []
  const hasMoreItems = order.items?.length > 3

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-semibold text-gray-900">
              Pedido #{order.id}
            </h3>
            {getStatusBadge(order.status)}
          </div>
          <p className="text-sm text-gray-600">
            {formatDate(order.created_at)}
          </p>
        </div>
        <div className="mt-2 md:mt-0 text-right">
          <p className="text-sm text-gray-600">Total</p>
          <p className="text-xl font-bold text-gray-900">
            {formatPrice(order.total_amount)}
          </p>
        </div>
      </div>

      {/* Items resumidos */}
      {displayedItems.length > 0 && (
        <div className="border-t pt-4 mb-4">
          <div className="space-y-2">
            {displayedItems.map((item, index) => (
              <div key={item.id} className="flex items-center gap-3">
                <OptimizedImage
                  src={getProductImage(item.product)}
                  alt={item.product?.name || item.product_name_snapshot}
                  className="w-12 h-12 object-cover rounded"
                  width={48}
                  height={48}
                  loading={index === 0 ? 'eager' : 'lazy'}
                  onError={(e) => {
                    e.target.src = '/placeholder-product.jpg'
                  }}
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {item.product?.name || item.product_name_snapshot || 'Producto'}
                  </p>
                  <p className="text-xs text-gray-600">
                    {item.quantity} x {formatPrice(item.unit_price)}
                  </p>
                </div>
                <p className="text-sm font-semibold text-gray-900">
                  {formatPrice(item.total_price)}
                </p>
              </div>
            ))}
            {hasMoreItems && (
              <p className="text-xs text-gray-500 text-center pt-2">
                +{order.items.length - 3} producto{order.items.length - 3 > 1 ? 's' : ''} más
              </p>
            )}
          </div>
        </div>
      )}

      {/* Footer con acciones */}
      <div className="flex justify-between items-center border-t pt-4">
        <div className="text-sm text-gray-600">
          <p>
            <span className="font-medium">Envío:</span>{' '}
            {order.shipping_cost === 0 ? (
              <span className="text-green-600 font-semibold">GRATIS</span>
            ) : (
              formatPrice(order.shipping_cost)
            )}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={onViewDetails}
        >
          Ver Detalles
        </Button>
      </div>
    </div>
  )
}

export default OrderCard

