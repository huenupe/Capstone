import { useState, useEffect, useCallback } from 'react'
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
import PriceTag from '../../components/products/PriceTag'
import { ordersService } from '../../services/orders'
import { usersService } from '../../services/users'
import { validatePostalCode } from '../../utils/validations'
import { REGIONS, getRegionLabel, matchRegionValue } from '../../constants/regions'

const CHECKOUT_STORAGE_KEY = 'checkout_data'

const StepAddress = () => {
  const navigate = useNavigate()
  const { isAuthenticated, user } = useAuthStore()
  const { items, subtotal, shipping, total, totalDiscount, updateTotals } = useCartStore()
  const { setDeliveryMethod, deliveryMethod } = useCheckoutStore()
  const [selectedDeliveryMethod, setSelectedDeliveryMethod] = useState(deliveryMethod || 'delivery')
  const [shippingQuote, setShippingQuote] = useState(null)
  const [loadingQuote, setLoadingQuote] = useState(false)
  const [savedAddresses, setSavedAddresses] = useState([])
  const [selectedAddressId, setSelectedAddressId] = useState(null)
  const [saveAddress, setSaveAddress] = useState(false)
  const [loadingAddresses, setLoadingAddresses] = useState(false)
  
  const storedCheckoutData = storage.get(CHECKOUT_STORAGE_KEY, !isAuthenticated)
  const storedAddress = storedCheckoutData?.address

  const defaultValues = storedAddress
    ? {
        ...storedAddress,
        region: matchRegionValue(storedAddress.region || ''),
      }
    : {
        street: user?.street || '',
        city: user?.city || '',
        region: matchRegionValue(user?.region || ''),
        postal_code: user?.postal_code || '',
        number: user?.number || '',
        apartment: user?.apartment || '',
      }

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm({
    defaultValues,
  })

  const watchedRegion = watch('region')

  useEffect(() => {
    if (user && isAuthenticated) {
      setValue('street', user.street || '')
      setValue('city', user.city || '')
      setValue('region', matchRegionValue(user.region || ''))
      setValue('postal_code', user.postal_code || '')
      setValue('number', user.number || '')
      setValue('apartment', user.apartment || '')
    }
  }, [user, isAuthenticated, setValue])

  // Obtener cotización cuando cambia la región o método de entrega
  useEffect(() => {
    // Solo ejecutar si estamos en modo delivery y hay región seleccionada
    if (!watchedRegion || selectedDeliveryMethod === 'pickup') {
      if (selectedDeliveryMethod === 'pickup') {
        setShippingQuote(null)
      }
      return
    }

    // Prevenir ejecución si no hay items
    if (!items || items.length === 0) {
      return
    }

    // Prevenir ejecución si no hay items válidos
    const validItems = items.filter(item => item?.product?.id || item?.product_id)
    if (validItems.length === 0) {
      return
    }

    let isMounted = true
    const timeoutId = setTimeout(async () => {
      if (!isMounted) return

      setLoadingQuote(true)
      try {
        // Obtener el label de la región (nombre completo)
        const regionName = getRegionLabel(watchedRegion)

        const cartItems = validItems.map(item => ({
          product_id: item.product?.id || item.product_id,
          quantity: item.quantity || 1,
        }))

        const quote = await ordersService.getShippingQuote({
          region: regionName,
          cart_items: cartItems,
          subtotal: subtotal || 0,
        })

        if (isMounted) {
          setShippingQuote(quote)
        }
      } catch (error) {
        if (isMounted) {
          console.error('Error fetching shipping quote:', error)
          // Usar valores por defecto si falla
          setShippingQuote({
            cost: subtotal >= 50000 ? 0 : 5000,
            free_shipping_threshold: 50000,
          })
        }
      } finally {
        if (isMounted) {
          setLoadingQuote(false)
        }
      }
    }, 500) // Debounce

    return () => {
      isMounted = false
      clearTimeout(timeoutId)
    }
  }, [watchedRegion, selectedDeliveryMethod, items, subtotal])

  // Asegurar que los totales estén actualizados cuando cambian los items
  useEffect(() => {
    if (items && items.length > 0 && updateTotals) {
      updateTotals()
    }
  }, [items, updateTotals])

  const selectAddress = useCallback((address) => {
    setSelectedAddressId(address.id)
    // Mapear región del backend al formato del frontend
    const regionValue = matchRegionValue(address.region)

    setValue('street', address.street || '')
    setValue('city', address.city || '')
    setValue('region', regionValue || '')
    setValue('postal_code', address.postal_code || '')
    setValue('number', address.number || '')
    setValue('apartment', address.apartment || '')
    
    // ✅ CORRECCIÓN: Guardar dirección seleccionada inmediatamente en storage
    const addressData = {
      street: address.street || '',
      city: address.city || '',
      region: regionValue || '',
      postal_code: address.postal_code || '',
      number: address.number || '',
      apartment: address.apartment || '',
    }
    
    const existingData = storage.get(CHECKOUT_STORAGE_KEY, !isAuthenticated) || {}
    storage.set(CHECKOUT_STORAGE_KEY, {
      ...existingData,
      address: {
        ...addressData,
        selected_address_id: address.id, // Guardar ID de dirección seleccionada
      },
      deliveryMethod: selectedDeliveryMethod,
    }, !isAuthenticated)
  }, [setSelectedAddressId, setValue, isAuthenticated, selectedDeliveryMethod])

  const handleNewAddress = useCallback(() => {
    setSelectedAddressId(null)
    setValue('street', '')
    setValue('city', '')
    setValue('region', '')
    setValue('postal_code', '')
    setValue('number', '')
    setValue('apartment', '')
  }, [setSelectedAddressId, setValue])

  const loadSavedAddresses = useCallback(async () => {
    setLoadingAddresses(true)
    try {
      const addresses = await usersService.getAddresses()
      setSavedAddresses(addresses || [])
      
      // Si hay una dirección por defecto, seleccionarla automáticamente
      const defaultAddress = addresses?.find(addr => addr.is_default)
      if (defaultAddress) {
        selectAddress(defaultAddress)
      }
    } catch (error) {
      console.error('Error loading saved addresses:', error)
    } finally {
      setLoadingAddresses(false)
    }
  }, [selectAddress])

  // Cargar direcciones guardadas si el usuario está autenticado
  useEffect(() => {
    if (isAuthenticated) {
      loadSavedAddresses()
    }
  }, [isAuthenticated, loadSavedAddresses])
  
  // ✅ CORRECCIÓN: Restaurar dirección seleccionada desde storage al cargar
  useEffect(() => {
    if (isAuthenticated && savedAddresses.length > 0 && !selectedAddressId) {
      const storedData = storage.get(CHECKOUT_STORAGE_KEY, false)
      const storedAddressId = storedData?.address?.selected_address_id
      
      if (storedAddressId && storedAddressId !== selectedAddressId) {
        const storedAddress = savedAddresses.find(addr => addr.id === storedAddressId)
        if (storedAddress) {
          setSelectedAddressId(storedAddressId)
          // Solo actualizar valores del formulario, no guardar en storage (ya está guardado)
          const regionValue = matchRegionValue(storedAddress.region)
          setValue('street', storedAddress.street || '')
          setValue('city', storedAddress.city || '')
          setValue('region', regionValue || '')
          setValue('postal_code', storedAddress.postal_code || '')
          setValue('number', storedAddress.number || '')
          setValue('apartment', storedAddress.apartment || '')
        }
      }
    }
  }, [isAuthenticated, savedAddresses, selectedAddressId, setValue])

  // Verificar que los pasos anteriores estén completos
  useEffect(() => {
    if (!isAuthenticated) {
      const storedData = storage.get(CHECKOUT_STORAGE_KEY, true)
      // Si es invitado y no tiene datos del cliente, redirigir a StepCustomer
      if (!storedData?.customer) {
        navigate('/checkout/customer')
        return
      }
    }
  }, [isAuthenticated, navigate])

  const onSubmit = async (data) => {
    // Si hay una dirección seleccionada, usar esa en lugar de los datos del formulario
    let addressData = data
    
    if (isAuthenticated && selectedAddressId) {
      const selectedAddress = savedAddresses.find(addr => addr.id === selectedAddressId)
      if (selectedAddress) {
        // Mapear región del backend al formato del frontend
        const regionValue = matchRegionValue(selectedAddress.region)
        
        addressData = {
          street: selectedAddress.street || '',
          city: selectedAddress.city || '',
          region: regionValue || '',
          postal_code: selectedAddress.postal_code || '',
          number: selectedAddress.number || '',
          apartment: selectedAddress.apartment || '',
        }
      }
    }
    
    // Save to storage
    const existingData = storage.get(CHECKOUT_STORAGE_KEY, !isAuthenticated) || {}
    storage.set(CHECKOUT_STORAGE_KEY, {
      ...existingData,
      address: {
        ...addressData,
        save_address: saveAddress && isAuthenticated && !selectedAddressId, // Solo guardar si es nueva dirección
      },
      deliveryMethod: selectedDeliveryMethod,
    }, !isAuthenticated)

    setDeliveryMethod(selectedDeliveryMethod)
    navigate('/checkout/payment')
  }
  
  // Función para manejar el envío cuando hay dirección seleccionada
  const handleContinueWithSelectedAddress = () => {
    // ✅ CORRECCIÓN: Validar que haya dirección antes de continuar
    if (isAuthenticated && selectedAddressId) {
      // Asegurar que la dirección esté guardada en storage
      const selectedAddress = savedAddresses.find(addr => addr.id === selectedAddressId)
      if (selectedAddress) {
        const regionValue = matchRegionValue(selectedAddress.region)
        const addressData = {
          street: selectedAddress.street || '',
          city: selectedAddress.city || '',
          region: regionValue || '',
          postal_code: selectedAddress.postal_code || '',
          number: selectedAddress.number || '',
          apartment: selectedAddress.apartment || '',
        }
        
        const existingData = storage.get(CHECKOUT_STORAGE_KEY, !isAuthenticated) || {}
        storage.set(CHECKOUT_STORAGE_KEY, {
          ...existingData,
          address: {
            ...addressData,
            selected_address_id: selectedAddressId,
          },
          deliveryMethod: selectedDeliveryMethod,
        }, !isAuthenticated)
      }
      onSubmit({})
    } else {
      // Validar formulario antes de continuar
      handleSubmit(onSubmit)()
    }
  }

  const handleDeliveryMethodChange = (method) => {
    setSelectedDeliveryMethod(method)
    setDeliveryMethod(method)
    // El useEffect se encargará de obtener la cotización si es necesario
  }

  const deliveryCost = selectedDeliveryMethod === 'pickup' 
    ? 0 
    : (shippingQuote?.cost ?? shipping)
  
  const freeShippingThreshold = shippingQuote?.free_shipping_threshold
  const amountNeeded = freeShippingThreshold && subtotal < freeShippingThreshold
    ? freeShippingThreshold - subtotal
    : null

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
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Dirección de Envío</h2>

              {isAuthenticated && loadingAddresses && (
                <div className="text-sm text-gray-500 mb-4">
                  Cargando direcciones guardadas...
                </div>
              )}

              {/* Dirección Guardada - Estilo Falabella */}
              {isAuthenticated && selectedAddressId && savedAddresses.length > 0 && (() => {
                const selectedAddress = savedAddresses.find(addr => addr.id === selectedAddressId)
                if (!selectedAddress) return null
                
                const addressText = [
                  selectedAddress.label && `Dirección - ${selectedAddress.label}`,
                  `${selectedAddress.street}${selectedAddress.number ? ` ${selectedAddress.number}` : ''}${selectedAddress.apartment ? `, Dpto ${selectedAddress.apartment}` : ''}`,
                  `${selectedAddress.city}, ${selectedAddress.region}${selectedAddress.postal_code ? `, ${selectedAddress.postal_code}` : ''}`
                ].filter(Boolean).join(', ')
                
                return (
                  <div className="mb-6 bg-white border border-gray-200 rounded-lg p-4 flex items-start gap-3">
                    {/* Ícono de ubicación */}
                    <svg 
                      className="w-5 h-5 text-gray-700 mt-0.5 flex-shrink-0" 
                      fill="currentColor" 
                      viewBox="0 0 20 20"
                      aria-hidden="true"
                    >
                      <path 
                        fillRule="evenodd" 
                        d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" 
                        clipRule="evenodd" 
                      />
                    </svg>
                    
                    {/* Texto de la dirección */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900 leading-relaxed">
                        {addressText}
                      </p>
                      {selectedAddress.is_default && (
                        <span className="inline-block mt-2 text-xs font-medium text-primary-600 bg-primary-50 px-2 py-1 rounded">
                          Predeterminada
                        </span>
                      )}
                    </div>
                    
                    {/* Botones de acción */}
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {/* Botón Cambiar */}
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedAddressId(null)
                          handleNewAddress()
                        }}
                        className="text-sm text-primary-600 hover:text-primary-700 underline font-medium transition-colors flex items-center gap-1"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                        Cambiar
                      </button>
                    </div>
                  </div>
                )
              })()}

              {/* Selector de direcciones guardadas (si no hay dirección seleccionada) */}
              {isAuthenticated && savedAddresses.length > 0 && !selectedAddressId && (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Selecciona una dirección guardada
                  </label>
                  <div className="space-y-2">
                    {savedAddresses.map((addr) => {
                      const addressText = `${addr.street}${addr.number ? ` ${addr.number}` : ''}${addr.apartment ? `, Dpto ${addr.apartment}` : ''}, ${addr.city}, ${addr.region}`
                      
                      return (
                        <div
                          key={addr.id}
                          className="border border-gray-200 rounded-lg p-3 hover:border-primary-300 hover:bg-primary-50 transition-colors cursor-pointer"
                          onClick={() => selectAddress(addr)}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex items-start gap-3 flex-1">
                              <svg 
                                className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" 
                                fill="currentColor" 
                                viewBox="0 0 20 20"
                              >
                                <path 
                                  fillRule="evenodd" 
                                  d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" 
                                  clipRule="evenodd" 
                                />
                              </svg>
                              <div className="flex-1 min-w-0">
                                {addr.label && (
                                  <p className="text-sm font-medium text-gray-900 mb-1">{addr.label}</p>
                                )}
                                <p className="text-sm text-gray-600">{addressText}</p>
                                {addr.is_default && (
                                  <span className="inline-block mt-1 text-xs font-medium text-primary-600">
                                    Predeterminada
                                  </span>
                                )}
                              </div>
                            </div>
                            <input
                              type="radio"
                              name="selectedAddress"
                              checked={selectedAddressId === addr.id}
                              onChange={() => selectAddress(addr)}
                              className="mt-1"
                            />
                          </div>
                        </div>
                      )
                    })}
                    <button
                      type="button"
                      onClick={handleNewAddress}
                      className="w-full border-2 border-dashed border-gray-300 rounded-lg p-3 text-sm text-gray-600 hover:border-primary-300 hover:text-primary-600 hover:bg-primary-50 transition-colors"
                    >
                      + Agregar nueva dirección
                    </button>
                  </div>
                </div>
              )}

              {/* Formulario de dirección - Solo se muestra si no hay dirección seleccionada o si el usuario quiere agregar una nueva */}
              {(!isAuthenticated || !selectedAddressId || (isAuthenticated && savedAddresses.length === 0)) && (
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
                        options={REGIONS}
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
                        validate: validatePostalCode,
                      }}
                      error={errors.postal_code?.message}
                      placeholder="1234567"
                    />
                  </div>

                  {/* Checkbox para guardar dirección (solo si está autenticado) */}
                  {isAuthenticated && !selectedAddressId && (
                    <div className="flex items-center space-x-2 pt-2">
                      <input
                        type="checkbox"
                        id="saveAddress"
                        checked={saveAddress}
                        onChange={(e) => setSaveAddress(e.target.checked)}
                        className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                      />
                      <label htmlFor="saveAddress" className="text-sm text-gray-700 cursor-pointer">
                        Guardar esta dirección para futuros pedidos
                      </label>
                    </div>
                  )}

                  {/* Solo botón "Atrás" aquí, "Ir a pagar" se movió al resumen */}
                  <div className="flex gap-4 pt-6">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => navigate(isAuthenticated ? '/cart' : '/checkout/customer')}
                      fullWidth
                    >
                      Atrás
                    </Button>
                  </div>
                </form>
              )}
            </div>

            {/* Método de Entrega - Siempre visible */}
            <div className="bg-white shadow-md rounded-lg p-6">
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
                          {loadingQuote ? (
                            <span className="text-gray-500 text-sm">Calculando...</span>
                          ) : deliveryCost === 0 ? (
                            <span className="text-green-600">GRATIS</span>
                          ) : (
                            formatPrice(deliveryCost)
                          )}
                        </span>
                      </div>
                      {loadingQuote ? (
                        <p className="text-sm text-gray-500 mt-1">Obteniendo cotización...</p>
                      ) : (
                        <>
                          <p className="text-sm text-gray-600 mt-1">
                            Entrega estimada: 2-3 días hábiles
                          </p>
                          {freeShippingThreshold && deliveryCost > 0 && (
                            <div className="mt-2 bg-blue-50 border border-blue-200 rounded-lg p-2">
                              <p className="text-xs text-blue-800">
                                Agrega {formatPrice(amountNeeded)} más para envío gratis
                              </p>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </div>
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
                        <div className="mt-1">
                          <PriceTag
                            price={item.unit_price || 0}
                            originalPrice={item.product?.has_discount ? item.product?.price : null}
                            discountPercent={item.product?.has_discount ? (item.product?.calculated_discount_percent || item.product?.discount_percent) : null}
                            size="sm"
                          />
                        </div>
                        <p className="text-xs text-gray-600 mt-1">
                          Cantidad: {item.quantity || 0}
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
                
                {totalDiscount > 0 && (
                  <div className="flex justify-between text-gray-700">
                    <span className="text-green-600">Descuentos</span>
                    <span className="text-green-600 font-semibold">-{formatPrice(totalDiscount || 0)}</span>
                  </div>
                )}
                
                <div className="flex justify-between text-gray-700">
                  <span>Entregas</span>
                  <span>
                    {loadingQuote ? (
                      <span className="text-gray-400 text-sm">...</span>
                    ) : deliveryCost === 0 ? (
                      <span className="text-green-600 font-semibold">GRATIS</span>
                    ) : (
                      formatPrice(deliveryCost)
                    )}
                  </span>
                </div>
                
                {freeShippingThreshold && deliveryCost > 0 && amountNeeded && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-2">
                    <div className="flex items-start">
                      <svg className="w-4 h-4 text-blue-600 mt-0.5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                      <p className="text-xs text-blue-800">
                        Agrega productos por {formatPrice(amountNeeded)} más para obtener envío gratis
                      </p>
                    </div>
                  </div>
                )}
                
                <div className="flex justify-between text-xl font-bold text-gray-900 border-t pt-2">
                  <span>Total</span>
                  <span>{formatPrice(total ?? ((subtotal || 0) + (deliveryCost || 0)))}</span>
                </div>
              </div>

              {/* Botón "Ir a pagar" movido aquí, debajo del resumen */}
              <div className="mt-6 pt-6 border-t">
                <Button
                  onClick={handleContinueWithSelectedAddress}
                  fullWidth
                  size="lg"
                >
                  Ir a pagar
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default StepAddress
