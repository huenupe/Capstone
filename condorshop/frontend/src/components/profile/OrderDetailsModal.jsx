import { Link } from 'react-router-dom'
import Modal from '../common/Modal'
import Button from '../common/Button'
import { formatPrice } from '../../utils/formatPrice'
import { getProductImage } from '../../utils/getProductImage'

const OrderDetailsModal = ({ order, onClose }) => {
  if (!order) return null

  const getStatusBadge = (status) => {
    // Mapeo de colores e iconos por código de estado (el label viene del backend en español)
    const statusConfig = {
      PENDING: { color: 'bg-yellow-100 text-yellow-800', icon: '⏳' },
      PAID: { color: 'bg-blue-100 text-blue-800', icon: '✓' },
      FAILED: { color: 'bg-red-100 text-red-800', icon: '✕' },
      CANCELLED: { color: 'bg-red-100 text-red-800', icon: '✕' },
      PREPARING: { color: 'bg-orange-100 text-orange-800', icon: '📦' },
      SHIPPED: { color: 'bg-purple-100 text-purple-800', icon: '🚚' },
      DELIVERED: { color: 'bg-green-100 text-green-800', icon: '✓' },
    }
    
    // Usar la descripción del backend (ya viene en español)
    const label = status?.description || status?.code || 'Desconocido'
    const config = statusConfig[status?.code] || { 
      color: 'bg-gray-100 text-gray-800',
      icon: '❓'
    }
    
    return (
      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-semibold ${config.color}`}>
        <span>{config.icon}</span>
        {label}
      </span>
    )
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('es-CL', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatAddress = () => {
    const parts = [
      order.shipping_street,
      order.shipping_city,
      order.shipping_region,
      order.shipping_postal_code,
    ].filter(Boolean)
    return parts.join(', ')
  }

  return (
    <Modal
      isOpen={!!order}
      onClose={onClose}
      title={`Detalle del Pedido #${order.id}`}
      size="lg"
      footer={
        <div className="flex justify-end gap-3">
          <Button variant="outline" onClick={onClose}>
            Cerrar
          </Button>
          <Link to="/">
            <Button>
              Seguir Comprando
            </Button>
          </Link>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Información general */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pb-4 border-b">
          <div>
            <p className="text-sm text-gray-600">Fecha del pedido</p>
            <p className="font-medium text-gray-900">{formatDate(order.created_at)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Estado</p>
            <div className="mt-1">
              {getStatusBadge(order.status)}
            </div>
          </div>
        </div>

        {/* Productos */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Productos</h3>
          <div className="space-y-3">
            {order.items?.map((item) => (
              <div
                key={item.id}
                className="flex items-start gap-4 p-3 bg-gray-50 rounded-lg"
              >
                <img
                  src={getProductImage(item.product)}
                  alt={item.product?.name || item.product_name_snapshot}
                  className="w-20 h-20 object-cover rounded"
                />
                <div className="flex-1 min-w-0">
                  {item.product?.slug ? (
                    <Link
                      to={`/product/${item.product.slug}`}
                      className="text-gray-900 hover:text-primary-600 font-medium block mb-1"
                    >
                      {item.product.name || item.product_name_snapshot}
                    </Link>
                  ) : (
                    <p className="text-gray-900 font-medium mb-1">
                      {item.product?.name || item.product_name_snapshot || 'Producto'}
                    </p>
                  )}
                  {item.product_sku_snapshot && (
                    <p className="text-xs text-gray-500 mb-1">
                      SKU: {item.product_sku_snapshot}
                    </p>
                  )}
                  <p className="text-sm text-gray-600">
                    Cantidad: {item.quantity} x {formatPrice(item.unit_price)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-gray-900">
                    {formatPrice(item.total_price)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Dirección de envío */}
        {(order.shipping_street || order.shipping_city) && (
          <div className="pt-4 border-t">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Dirección de envío</h3>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-gray-900 font-medium mb-1">
                {order.customer_name || 'Cliente'}
              </p>
              {order.customer_email && (
                <p className="text-sm text-gray-600 mb-1">{order.customer_email}</p>
              )}
              {order.customer_phone && (
                <p className="text-sm text-gray-600 mb-2">{order.customer_phone}</p>
              )}
              <p className="text-sm text-gray-700">{formatAddress()}</p>
            </div>
          </div>
        )}

        {/* Resumen de pago */}
        <div className="pt-4 border-t">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Resumen</h3>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Subtotal</span>
              <span className="text-gray-900">
                {formatPrice(order.total_amount - (order.shipping_cost || 0))}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Envío</span>
              <span className={order.shipping_cost === 0 ? 'text-green-600 font-semibold' : 'text-gray-900'}>
                {order.shipping_cost === 0 ? 'GRATIS' : formatPrice(order.shipping_cost)}
              </span>
            </div>
            <div className="flex justify-between text-lg font-bold pt-2 border-t">
              <span className="text-gray-900">Total</span>
              <span className="text-gray-900">{formatPrice(order.total_amount)}</span>
            </div>
          </div>
        </div>
      </div>
    </Modal>
  )
}

export default OrderDetailsModal

