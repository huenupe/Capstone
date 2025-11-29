import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Button from '../../components/common/Button'
import CheckoutStepper from '../../components/checkout/CheckoutStepper'
import { useAuthStore } from '../../store/authSlice'
import { useCartStore } from '../../store/cartSlice'
import { useCheckoutStore } from '../../store/checkoutSlice'
import { storage } from '../../utils/storage'
import { formatPrice } from '../../utils/formatPrice'
import { getProductImage } from '../../utils/getProductImage'
import webpayBanner from '../../assets/Webpay.png'

const CHECKOUT_STORAGE_KEY = 'checkout_data'

const StepPayment = () => {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuthStore()
  const { items, subtotal, shipping, total } = useCartStore()
  const { paymentMethod, setPaymentMethod, canPay, deliveryMethod } = useCheckoutStore()
  
  // Verificar que los pasos anteriores estén completos
  useEffect(() => {
    const storedData = storage.get(CHECKOUT_STORAGE_KEY, !isAuthenticated)
    if (!storedData?.address) {
      navigate('/checkout/address')
    }
    if (!isAuthenticated && !storedData?.customer) {
      navigate('/checkout/customer')
    }
  }, [navigate, isAuthenticated])

  // Flag para habilitar Webpay - manejo seguro de variable de entorno
  const webpayEnabled = import.meta.env.VITE_WEBPAY_ENABLED === 'true'
  // El botón se habilita cuando Webpay está habilitado Y se ha seleccionado Webpay como método de pago
  const canProceed = webpayEnabled && paymentMethod === 'webpay'

  const deliveryCost = deliveryMethod === 'pickup' ? 0 : shipping

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <CheckoutStepper currentStep="payment" isAuthenticated={isAuthenticated} />
          <h1 className="text-2xl font-bold text-center text-gray-900">
            Método de Pago
          </h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Columna Izquierda: Métodos de Pago */}
          <div className="lg:col-span-2">
            <div className="bg-white shadow-md rounded-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Elegir método de pago</h2>
              
              <div className="space-y-4">
                {/* Webpay Plus */}
                <div
                  className={`border rounded-lg p-4 md:p-6 cursor-pointer transition-colors ${
                    paymentMethod === 'webpay'
                      ? 'border-primary-600 bg-primary-50'
                      : 'border-slate-200 bg-white shadow-sm hover:border-gray-400'
                  } ${!webpayEnabled ? 'opacity-60 cursor-not-allowed' : ''}`}
                  onClick={() => webpayEnabled && setPaymentMethod('webpay')}
                  role="radio"
                  aria-checked={paymentMethod === 'webpay'}
                  aria-disabled={!webpayEnabled}
                  tabIndex={webpayEnabled ? 0 : -1}
                  onKeyDown={(e) => {
                    if (webpayEnabled && (e.key === 'Enter' || e.key === ' ')) {
                      e.preventDefault()
                      setPaymentMethod('webpay')
                    }
                  }}
                >
                  {/* Layout responsive: mobile (columna) / desktop (fila) */}
                  <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    {/* Columna izquierda: radio + textos */}
                    <div className="flex-1">
                      <label className="flex items-center gap-3 cursor-pointer">
                        <input
                          type="radio"
                          name="paymentMethod"
                          checked={paymentMethod === 'webpay'}
                          onChange={() => webpayEnabled && setPaymentMethod('webpay')}
                          disabled={!webpayEnabled}
                          className="flex-shrink-0"
                        />
                        <span className="text-lg font-semibold text-gray-900">Webpay Plus</span>
                      </label>
                      
                      <p className="mt-2 text-sm text-slate-700">
                        Tarjetas crédito/débito/prepago. Transacción segura con Transbank.
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        Tus datos de tarjeta se procesan de forma segura por la pasarela; CondorShop no almacena esta información.
                      </p>
                    </div>
                    
                    {/* Columna derecha: banner único de Webpay Plus */}
                    <div className="mt-2 md:mt-0 flex justify-center md:justify-end flex-shrink-0">
                      <img
                        src={webpayBanner}
                        alt="Webpay Plus - Transbank"
                        className="h-12 md:h-14 w-auto object-contain"
                      />
                    </div>
                  </div>
                </div>

                {/* Otros métodos (deshabilitado) */}
                <div
                  className="border rounded-lg p-6 opacity-60 cursor-not-allowed"
                  role="radio"
                  aria-checked={false}
                  aria-disabled={true}
                >
                  <div className="flex items-start">
                    <input
                      type="radio"
                      name="paymentMethod"
                      disabled
                      className="mt-1"
                    />
                    <div className="ml-4 flex-1">
                      <div className="flex items-center justify-between">
                        <h3 className="text-lg font-semibold text-gray-900">Otros</h3>
                      </div>
                      <p className="text-sm text-gray-600 mt-2">
                        Otros métodos de pago estarán disponibles en el futuro.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-6 border-t">
                <Button
                  onClick={() => {
                    if (canProceed) {
                      navigate('/checkout/review')
                    }
                  }}
                  fullWidth
                  size="lg"
                  disabled={!canProceed}
                  title={!canProceed ? (webpayEnabled ? 'Selecciona un método de pago' : 'Webpay no está habilitado aún') : ''}
                >
                  Continuar
                </Button>
              </div>
            </div>
          </div>

          {/* Columna Derecha: Resumen de la compra */}
          <div className="lg:col-span-1">
            <div className="bg-white shadow-md rounded-lg p-6 sticky top-4">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Resumen de la compra</h2>
              
              <div className="space-y-4 mb-4">
                {Array.isArray(items) && items.length > 0 ? (
                  items.map((item) => (
                    <div key={item.id || item.product_id} className="flex items-center gap-3 border-b pb-3">
                      <img
                        src={getProductImage(item.product)}
                        alt={item.product?.name || 'Producto'}
                        className="w-12 h-12 object-cover rounded"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {item.product?.name || 'Producto'}
                        </p>
                        <p className="text-xs text-gray-600">
                          {item.quantity || 0} x {formatPrice(item.unit_price || 0)}
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-gray-500 text-center py-4">No hay productos en el carrito</p>
                )}
              </div>

              <div className="space-y-2 border-t pt-4">
                <div className="flex justify-between text-gray-700">
                  <span>Productos ({Array.isArray(items) ? items.length : 0})</span>
                  <span>{formatPrice(subtotal || 0)}</span>
                </div>
                
                <div className="flex justify-between text-gray-700">
                  <span>Descuentos</span>
                  <span>{formatPrice(0)}</span>
                </div>
                
                <div className="flex justify-between text-gray-700">
                  <span>Entregas</span>
                  <span>
                    {deliveryCost === 0 ? (
                      <span className="text-green-600 font-semibold">GRATIS</span>
                    ) : (
                      formatPrice(deliveryCost)
                    )}
                  </span>
                </div>
                
                <div className="flex justify-between text-xl font-bold text-gray-900 border-t pt-2">
                  <span>Total</span>
                  <span>{formatPrice(total ?? ((subtotal ?? 0) + (deliveryCost ?? 0)))}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default StepPayment

