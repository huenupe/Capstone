import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import Button from '../../components/common/Button'
import TextField from '../../components/forms/TextField'
import Select from '../../components/forms/Select'
import CheckoutStepper from '../../components/checkout/CheckoutStepper'
import { useAuthStore } from '../../store/authSlice'
import { useCartStore } from '../../store/cartSlice'
import { useCheckoutStore } from '../../store/checkoutSlice'
import { storage } from '../../utils/storage'
import { formatPrice } from '../../utils/formatPrice'
import { getProductImage } from '../../utils/getProductImage'

const CHECKOUT_STORAGE_KEY = 'checkout_data'

const regions = [
  { value: 'arica', label: 'Arica y Parinacota' },
  { value: 'tarapaca', label: 'Tarapacá' },
  { value: 'antofagasta', label: 'Antofagasta' },
  { value: 'atacama', label: 'Atacama' },
  { value: 'coquimbo', label: 'Coquimbo' },
  { value: 'valparaiso', label: "Valparaíso" },
  { value: 'metropolitana', label: 'Región Metropolitana' },
  { value: 'ohiggins', label: "O'Higgins" },
  { value: 'maule', label: 'Maule' },
  { value: 'nuble', label: 'Ñuble' },
  { value: 'biobio', label: 'Biobío' },
  { value: 'araucania', label: 'La Araucanía' },
  { value: 'rios', label: 'Los Ríos' },
  { value: 'lagos', label: 'Los Lagos' },
  { value: 'aysen', label: 'Aysén' },
  { value: 'magallanes', label: 'Magallanes' },
]

const StepAddress = () => {
  const navigate = useNavigate()
  const { isAuthenticated, user } = useAuthStore()
  const { items, subtotal, shipping, total } = useCartStore()
  const { setDeliveryMethod, deliveryMethod } = useCheckoutStore()
  const [showAddressModal, setShowAddressModal] = useState(false)
  const [selectedDeliveryMethod, setSelectedDeliveryMethod] = useState(deliveryMethod || 'delivery')
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm({
    defaultValues: storage.get(CHECKOUT_STORAGE_KEY, !isAuthenticated)?.address || {
      street: user?.street || '',
      city: user?.city || '',
      region: user?.region || '',
      postal_code: user?.postal_code || '',
      number: user?.number || '',
      apartment: user?.apartment || '',
    },
  })

  const watchedRegion = watch('region')

  useEffect(() => {
    if (user && isAuthenticated) {
      setValue('street', user.street || '')
      setValue('city', user.city || '')
      setValue('region', user.region || '')
      setValue('postal_code', user.postal_code || '')
      setValue('number', user.number || '')
      setValue('apartment', user.apartment || '')
    }
  }, [user, isAuthenticated, setValue])

  // Verificar si hay dirección guardada
  useEffect(() => {
    const storedData = storage.get(CHECKOUT_STORAGE_KEY, !isAuthenticated)
    if (!storedData?.address && !isAuthenticated) {
      // Si es invitado y no tiene dirección, mostrar modal
      setShowAddressModal(true)
    }
  }, [isAuthenticated])

  const onSubmit = async (data) => {
    // Save to storage
    const existingData = storage.get(CHECKOUT_STORAGE_KEY, !isAuthenticated) || {}
    storage.set(CHECKOUT_STORAGE_KEY, {
      ...existingData,
      address: data,
      deliveryMethod: selectedDeliveryMethod,
    }, !isAuthenticated)

    setDeliveryMethod(selectedDeliveryMethod)
    navigate('/checkout/payment')
  }

  const handleDeliveryMethodChange = (method) => {
    setSelectedDeliveryMethod(method)
    setDeliveryMethod(method)
  }

  const deliveryCost = selectedDeliveryMethod === 'pickup' ? 0 : shipping

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <CheckoutStepper currentStep="address" isAuthenticated={isAuthenticated} />
          <h1 className="text-2xl font-bold text-center text-gray-900">
            Dirección y Entrega
          </h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Columna Izquierda: Dirección y Método de Entrega */}
          <div className="lg:col-span-2 space-y-6">
            {/* Dirección */}
            <div className="bg-white shadow-md rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Dirección de Envío</h2>
                {isAuthenticated && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAddressModal(true)}
                  >
                    Cambiar
                  </Button>
                )}
              </div>

              <form onSubmit={handleSubmit(onSubmit)}>
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Select
                      label="Región"
                      name="region"
                      register={register}
                      validation={{
                        required: 'La región es requerida',
                      }}
                      error={errors.region?.message}
                      options={regions}
                      placeholder="Selecciona una región"
                    />

                    <TextField
                      label="Comuna"
                      name="city"
                      type="text"
                      register={register}
                      validation={{
                        required: 'La comuna es requerida',
                      }}
                      error={errors.city?.message}
                      placeholder="Selecciona una comuna"
                    />
                  </div>

                  <TextField
                    label="Calle"
                    name="street"
                    type="text"
                    register={register}
                    validation={{
                      required: 'La calle es requerida',
                    }}
                    error={errors.street?.message}
                    placeholder="Ingresa el nombre de la calle"
                  />

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <TextField
                      label="Número"
                      name="number"
                      type="text"
                      register={register}
                      validation={{
                        required: 'El número es requerido',
                      }}
                      error={errors.number?.message}
                      placeholder="Ingresa el número de la calle"
                    />

                    <TextField
                      label="Dpto/Casa/Oficina"
                      name="apartment"
                      type="text"
                      register={register}
                      error={errors.apartment?.message}
                      placeholder="Opcional"
                    />
                  </div>

                  <TextField
                    label="Código Postal"
                    name="postal_code"
                    type="text"
                    register={register}
                    validation={{
                      required: 'El código postal es requerido',
                    }}
                    error={errors.postal_code?.message}
                    placeholder="1234567"
                  />
                </div>

                {/* Método de Entrega */}
                <div className="mt-6 pt-6 border-t">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Método de Entrega</h3>
                  
                  <div className="space-y-4">
                    {/* Retiro en punto */}
                    <div
                      className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                        selectedDeliveryMethod === 'pickup'
                          ? 'border-primary-600 bg-primary-50'
                          : 'border-gray-300 hover:border-gray-400'
                      }`}
                      onClick={() => handleDeliveryMethodChange('pickup')}
                      role="radio"
                      aria-checked={selectedDeliveryMethod === 'pickup'}
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          handleDeliveryMethodChange('pickup')
                        }
                      }}
                    >
                      <div className="flex items-start">
                        <input
                          type="radio"
                          name="deliveryMethod"
                          checked={selectedDeliveryMethod === 'pickup'}
                          onChange={() => handleDeliveryMethodChange('pickup')}
                          className="mt-1"
                        />
                        <div className="ml-3 flex-1">
                          <div className="flex items-center justify-between">
                            <h4 className="font-medium text-gray-900">Retiro en un punto</h4>
                            <span className="text-green-600 font-semibold">GRATIS</span>
                          </div>
                          <p className="text-sm text-gray-600 mt-1">
                            Selecciona una tienda cercana para retirar tu pedido
                          </p>
                          {/* Mock: Selector de tienda */}
                          <select className="mt-2 w-full px-3 py-2 border border-gray-300 rounded-lg">
                            <option>Selecciona una tienda (mock)</option>
                            <option>Tienda Centro - Av. Principal 123</option>
                            <option>Tienda Norte - Calle Norte 456</option>
                          </select>
                          <p className="text-xs text-gray-500 mt-1">
                            Fecha disponible: Próximamente (mock)
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Envío a domicilio */}
                    <div
                      className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                        selectedDeliveryMethod === 'delivery'
                          ? 'border-primary-600 bg-primary-50'
                          : 'border-gray-300 hover:border-gray-400'
                      }`}
                      onClick={() => handleDeliveryMethodChange('delivery')}
                      role="radio"
                      aria-checked={selectedDeliveryMethod === 'delivery'}
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          handleDeliveryMethodChange('delivery')
                        }
                      }}
                    >
                      <div className="flex items-start">
                        <input
                          type="radio"
                          name="deliveryMethod"
                          checked={selectedDeliveryMethod === 'delivery'}
                          onChange={() => handleDeliveryMethodChange('delivery')}
                          className="mt-1"
                        />
                        <div className="ml-3 flex-1">
                          <div className="flex items-center justify-between">
                            <h4 className="font-medium text-gray-900">Envío a domicilio</h4>
                            <span className="text-gray-900 font-semibold">
                              {deliveryCost === 0 ? (
                                <span className="text-green-600">GRATIS</span>
                              ) : (
                                formatPrice(deliveryCost)
                              )}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 mt-1">
                            Entrega estimada: 2-3 días hábiles (mock)
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
                            Franja horaria: 9:00 - 18:00 (mock)
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex gap-4 pt-6">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => navigate(isAuthenticated ? '/cart' : '/checkout/customer')}
                    fullWidth
                  >
                    Atrás
                  </Button>
                  <Button type="submit" fullWidth>
                    Ir a pagar
                  </Button>
                </div>
              </form>
            </div>
          </div>

          {/* Columna Derecha: Resumen de la compra */}
          <div className="lg:col-span-1">
            <div className="bg-white shadow-md rounded-lg p-6 sticky top-4">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Resumen de la compra</h2>
              
              <div className="space-y-4 mb-4">
                {items.map((item) => (
                  <div key={item.id} className="flex items-center gap-3 border-b pb-3">
                    <img
                      src={getProductImage(item.product)}
                      alt={item.product?.name}
                      className="w-12 h-12 object-cover rounded"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {item.product?.name}
                      </p>
                      <p className="text-xs text-gray-600">
                        {item.quantity} x {formatPrice(item.unit_price)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="space-y-2 border-t pt-4">
                <div className="flex justify-between text-gray-700">
                  <span>Productos ({items.length})</span>
                  <span>{formatPrice(subtotal)}</span>
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
                  <span>{formatPrice(subtotal + deliveryCost)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default StepAddress
