import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { formatPrice } from '../../utils/formatPrice'
import { getProductImage } from '../../utils/getProductImage'
import Button from '../../components/common/Button'
import Spinner from '../../components/common/Spinner'
import { ordersService } from '../../services/orders'
import { useCartStore } from '../../store/cartSlice'
import { useAuthStore } from '../../store/authSlice'
import { useToast } from '../../components/common/Toast'
import { storage } from '../../utils/storage'

const CHECKOUT_STORAGE_KEY = 'checkout_data'

const StepReview = () => {
  const navigate = useNavigate()
  const { items, subtotal, shipping, total, clearCart } = useCartStore()
  const [loading, setLoading] = useState(false)
  const [orderData, setOrderData] = useState(null)
  const toast = useToast()

  const { isAuthenticated } = useAuthStore()

  useEffect(() => {
    const storedData = storage.get(CHECKOUT_STORAGE_KEY, !isAuthenticated)
    if (!storedData?.address) {
      navigate('/checkout/address')
      return
    }
    if (!isAuthenticated && !storedData?.customer) {
      navigate('/checkout/customer')
      return
    }
  }, [navigate, isAuthenticated])

  const checkoutData = storage.get(CHECKOUT_STORAGE_KEY, !isAuthenticated) || {}

  const handleCreateOrder = async () => {
    if (!checkoutData.customer || !checkoutData.address) {
      toast.error('Por favor completa todos los pasos')
      navigate('/checkout/customer')
      return
    }

    setLoading(true)
    try {
      const orderPayload = {
        customer_email: checkoutData.customer.email,
        customer_first_name: checkoutData.customer.first_name,
        customer_last_name: checkoutData.customer.last_name,
        customer_phone: checkoutData.customer.phone,
        street: checkoutData.address.street,
        city: checkoutData.address.city,
        region: checkoutData.address.region,
        postal_code: checkoutData.address.postal_code,
      }

      const order = await ordersService.createOrder(orderPayload)
      setOrderData(order)
      
      // Clear cart and checkout data
      clearCart()
      storage.remove(CHECKOUT_STORAGE_KEY, !isAuthenticated)
      
      toast.success('¡Pedido creado exitosamente!')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Error al crear el pedido')
      console.error('Error creating order:', error)
    } finally {
      setLoading(false)
    }
  }

  if (orderData) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white shadow-md rounded-lg p-8 text-center">
            <div className="mb-6">
              <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                ¡Pedido Confirmado!
              </h2>
              <p className="text-gray-600">
                Tu pedido ha sido creado exitosamente
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-6 mb-6">
              <p className="text-sm text-gray-600 mb-2">Número de Pedido</p>
              <p className="text-3xl font-bold text-primary-600">
                #{orderData.order_number || orderData.id}
              </p>
            </div>

            <div className="text-left bg-gray-50 rounded-lg p-6 mb-6">
              <h3 className="font-semibold text-gray-900 mb-3">Resumen del Pedido</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Subtotal:</span>
                  <span>{formatPrice(subtotal)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Envío:</span>
                  <span>{shipping === 0 ? 'GRATIS' : formatPrice(shipping)}</span>
                </div>
                <div className="flex justify-between font-bold text-lg border-t pt-2">
                  <span>Total:</span>
                  <span>{formatPrice(total)}</span>
                </div>
              </div>
            </div>

            <div className="flex gap-4">
              <Button
                variant="outline"
                onClick={() => navigate('/')}
                fullWidth
              >
                Seguir Comprando
              </Button>
              {useAuthStore.getState().isAuthenticated && (
                <Button
                  onClick={() => navigate('/orders')}
                  fullWidth
                >
                  Ver Mis Pedidos
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <div className="flex items-center justify-center mb-4">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-green-500 text-white rounded-full flex items-center justify-center font-semibold">
                ✓
              </div>
              <div className="w-24 h-1 bg-primary-600"></div>
              <div className="w-10 h-10 bg-green-500 text-white rounded-full flex items-center justify-center font-semibold">
                ✓
              </div>
              <div className="w-24 h-1 bg-primary-600"></div>
              <div className="w-10 h-10 bg-primary-600 text-white rounded-full flex items-center justify-center font-semibold">
                3
              </div>
            </div>
          </div>
          <h1 className="text-2xl font-bold text-center text-gray-900">
            Revisar y Confirmar
          </h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Customer & Address Info */}
          <div className="space-y-6">
            <div className="bg-white shadow-md rounded-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Datos del Cliente</h2>
              <div className="space-y-2 text-sm">
                <p>
                  <span className="font-medium">Email:</span> {checkoutData.customer?.email}
                </p>
                <p>
                  <span className="font-medium">Nombre:</span>{' '}
                  {checkoutData.customer?.first_name} {checkoutData.customer?.last_name}
                </p>
                <p>
                  <span className="font-medium">Teléfono:</span> {checkoutData.customer?.phone}
                </p>
              </div>
            </div>

            <div className="bg-white shadow-md rounded-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Dirección de Envío</h2>
              <div className="space-y-2 text-sm">
                <p>{checkoutData.address?.street}</p>
                <p>
                  {checkoutData.address?.city}, {checkoutData.address?.region}
                </p>
                <p>
                  <span className="font-medium">Código Postal:</span>{' '}
                  {checkoutData.address?.postal_code}
                </p>
              </div>
            </div>
          </div>

          {/* Order Summary */}
          <div className="bg-white shadow-md rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Resumen del Pedido</h2>
            
            <div className="space-y-4 mb-6">
              {items.map((item) => (
                <div key={item.id} className="flex items-center gap-4 border-b pb-4">
                  <img
                    src={getProductImage(item.product)}
                    alt={item.product?.name}
                    className="w-16 h-16 object-cover rounded"
                  />
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{item.product?.name}</p>
                    <p className="text-sm text-gray-600">
                      {item.quantity} x {formatPrice(item.unit_price)}
                    </p>
                  </div>
                  <p className="font-semibold text-gray-900">
                    {formatPrice(item.unit_price * item.quantity)}
                  </p>
                </div>
              ))}
            </div>

            <div className="space-y-2 border-t pt-4">
              <div className="flex justify-between text-gray-700">
                <span>Subtotal</span>
                <span>{formatPrice(subtotal)}</span>
              </div>
              <div className="flex justify-between text-gray-700">
                <span>Envío</span>
                <span>
                  {shipping === 0 ? (
                    <span className="text-green-600 font-semibold">GRATIS</span>
                  ) : (
                    formatPrice(shipping)
                  )}
                </span>
              </div>
              {subtotal >= 50000 && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-2 text-sm text-green-800">
                  🎉 ¡Envío gratis!
                </div>
              )}
              <div className="flex justify-between text-xl font-bold text-gray-900 border-t pt-2">
                <span>Total</span>
                <span>{formatPrice(total)}</span>
              </div>
            </div>

            <div className="mt-6 space-y-4">
              <Button
                onClick={handleCreateOrder}
                fullWidth
                size="lg"
                disabled={loading}
              >
                {loading ? <Spinner size="sm" /> : 'Crear Pedido'}
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate('/checkout/address')}
                fullWidth
              >
                Atrás
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default StepReview

