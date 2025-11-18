import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { formatPrice } from '../../utils/formatPrice'
import { getProductImage } from '../../utils/getProductImage'
import Button from '../../components/common/Button'
import Spinner from '../../components/common/Spinner'
import { ordersService } from '../../services/orders'
import paymentsService from '../../services/paymentsService'
import { useCartStore } from '../../store/cartSlice'
import { useAuthStore } from '../../store/authSlice'
import { useToast } from '../../components/common/Toast'
import { storage } from '../../utils/storage'
import { getRegionLabel } from '../../constants/regions'

const CHECKOUT_STORAGE_KEY = 'checkout_data'

const StepReview = () => {
  const navigate = useNavigate()
  const { items, subtotal, shipping, total, clearCart } = useCartStore()
  const [isCreatingOrder, setIsCreatingOrder] = useState(false)
  const [orderData, setOrderData] = useState(null)
  const [error, setError] = useState(null)
  const toast = useToast()

  const { isAuthenticated, user } = useAuthStore()

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
  
  // ✅ CORRECCIÓN: Obtener datos del cliente (usuario autenticado o datos del storage)
  const customerData = isAuthenticated && user
    ? {
        email: user.email || '',
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        phone: user.phone || '',
      }
    : checkoutData.customer || {}

  const handleCreateOrder = async () => {
    // ✅ CORRECCIÓN: Validar con customerData en lugar de checkoutData.customer
    if (!customerData.email || !customerData.first_name || !checkoutData.address) {
      toast.error('Por favor completa todos los pasos')
      if (!isAuthenticated) {
        navigate('/checkout/customer')
      } else {
        navigate('/checkout/address')
      }
      return
    }

    setIsCreatingOrder(true)
    setError(null)

    try {
      // 1. Crear la orden (estado PENDING)
      console.log('Creando orden...', { customerData, address: checkoutData.address })
      
      // Mapear región del frontend al formato del backend (nombre completo)
      const regionLabel = getRegionLabel(checkoutData.address.region)

      const orderPayload = {
        customer_name: `${customerData.first_name} ${customerData.last_name}`,
        customer_email: customerData.email,
        customer_phone: customerData.phone || '',
        shipping_street: checkoutData.address.street,
        shipping_city: checkoutData.address.city,
        shipping_region: regionLabel,
        shipping_postal_code: checkoutData.address.postal_code || '',
        // Guardar dirección si el usuario está autenticado y lo solicitó
        save_address: checkoutData.address.save_address || false,
        address_label: checkoutData.address.save_address ? (checkoutData.address.label || '') : '',
      }

      const order = await ordersService.createOrder(orderPayload)
      console.log('Orden creada:', order)
      
      setOrderData(order)

      // 2. Verificar si Webpay está habilitado
      const webpayEnabled = import.meta.env.VITE_WEBPAY_ENABLED === 'true'
      
      if (!webpayEnabled) {
        // Modo legacy: mostrar confirmación sin pago
        console.warn('Webpay deshabilitado. Mostrando confirmación sin pago.')
        clearCart()
        storage.remove(CHECKOUT_STORAGE_KEY, !isAuthenticated)
        toast.success('¡Pedido creado exitosamente!')
        setIsCreatingOrder(false)
        return
      }

      // 3. Iniciar pago con Webpay
      console.log('Iniciando pago Webpay para orden:', order.id)
      
      try {
        const paymentResponse = await paymentsService.initiateWebpayPayment(order.id)
        console.log('Respuesta de Webpay:', paymentResponse)

        // 4. Redirigir a Webpay
        if (paymentResponse.success && paymentResponse.token && paymentResponse.url) {
          // Guardar order_id en sessionStorage para recuperarlo al volver
          sessionStorage.setItem('pending_order_id', order.id)
          sessionStorage.setItem('pending_order_amount', order.total_amount)
          
          // Clear cart and checkout data antes de redirigir
          clearCart()
          storage.remove(CHECKOUT_STORAGE_KEY, !isAuthenticated)
          
          console.log('Redirigiendo a Webpay...')
          
          // Pequeño delay para que el usuario vea el mensaje
          setTimeout(() => {
            paymentsService.redirectToWebpay(paymentResponse.token, paymentResponse.url)
          }, 1000)
          
        } else {
          throw new Error('Respuesta inválida de Webpay')
        }
        
      } catch (paymentError) {
        console.error('Error al iniciar pago:', paymentError)
        setError(
          'No se pudo iniciar el pago. Por favor, intenta nuevamente o contacta con soporte.'
        )
        setIsCreatingOrder(false)
        toast.error(paymentError.response?.data?.error || 'Error al iniciar el pago')
      }

    } catch (orderError) {
      console.error('Error al crear orden:', orderError)
      setError(
        orderError.response?.data?.error || 
        'Error al crear la orden. Por favor, intenta nuevamente.'
      )
      setIsCreatingOrder(false)
      toast.error(orderError.response?.data?.error || 'Error al crear el pedido')
    }
  }

  // Si Webpay está habilitado, no mostrar confirmación aquí (redirige a Webpay)
  const webpayEnabled = import.meta.env.VITE_WEBPAY_ENABLED === 'true'
  
  if (orderData && !webpayEnabled) {
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
    <>
      {/* Modal de carga cuando está creando orden o redirigiendo */}
      {isCreatingOrder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-lg shadow-xl max-w-md">
            <div className="flex flex-col items-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-4"></div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">
                {orderData ? 'Redirigiendo a Webpay...' : 'Creando tu orden...'}
              </h3>
              <p className="text-gray-600 text-center">
                {orderData 
                  ? 'Serás redirigido al sitio de pago seguro de Transbank.'
                  : 'Por favor espera mientras procesamos tu solicitud.'
                }
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Mensaje de error */}
      {error && (
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 mb-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error}</p>
          </div>
        </div>
      )}

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
                  <span className="font-medium">Email:</span> {customerData?.email || 'No especificado'}
                </p>
                <p>
                  <span className="font-medium">Nombre:</span>{' '}
                  {customerData?.first_name || ''} {customerData?.last_name || ''}
                </p>
                <p>
                  <span className="font-medium">Teléfono:</span> {customerData?.phone || 'No especificado'}
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
              {Array.isArray(items) && items.length > 0 ? (
                items.map((item) => (
                  <div key={item.id || item.product_id} className="flex items-center gap-4 border-b pb-4">
                    <img
                      src={getProductImage(item.product)}
                      alt={item.product?.name || 'Producto'}
                      className="w-16 h-16 object-cover rounded"
                    />
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{item.product?.name || 'Producto'}</p>
                      <p className="text-sm text-gray-600">
                        {item.quantity || 0} x {formatPrice(item.unit_price || 0)}
                      </p>
                    </div>
                    <p className="font-semibold text-gray-900">
                      {formatPrice((item.unit_price || 0) * (item.quantity || 0))}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-500 text-center py-4">No hay productos en el carrito</p>
              )}
            </div>

            <div className="space-y-2 border-t pt-4">
              <div className="flex justify-between text-gray-700">
                <span>Subtotal</span>
                <span>{formatPrice(subtotal || 0)}</span>
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
                disabled={isCreatingOrder}
              >
                {isCreatingOrder ? <Spinner size="sm" /> : 'Crear Pedido'}
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
    </>
  )
}

export default StepReview

