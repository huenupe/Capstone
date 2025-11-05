import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import Button from '../../components/common/Button'
import TextField from '../../components/forms/TextField'
import CheckoutStepper from '../../components/checkout/CheckoutStepper'
import { useAuthStore } from '../../store/authSlice'
import { storage } from '../../utils/storage'
import { validateEmail, validateOnlyLetters, validateChileanPhone } from '../../utils/validations'

const CHECKOUT_STORAGE_KEY = 'checkout_data'

const StepCustomer = () => {
  const navigate = useNavigate()
  const { isAuthenticated, user } = useAuthStore()
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
  } = useForm({
    defaultValues: storage.get(CHECKOUT_STORAGE_KEY, !isAuthenticated)?.customer || {
      email: user?.email || '',
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      phone: user?.phone || '',
    },
  })

  useEffect(() => {
    if (user) {
      setValue('email', user.email || '')
      setValue('first_name', user.first_name || '')
      setValue('last_name', user.last_name || '')
      setValue('phone', user.phone || '')
    }
  }, [user, setValue])

  const onSubmit = async (data) => {
    // Save to storage (usar sessionStorage para invitados)
    const existingData = storage.get(CHECKOUT_STORAGE_KEY, !isAuthenticated) || {}
    storage.set(CHECKOUT_STORAGE_KEY, {
      ...existingData,
      customer: data,
    }, !isAuthenticated)

    navigate('/checkout/address')
  }

  // Si el usuario está autenticado, redirigir a dirección (este paso solo para invitados)
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/checkout/address')
    }
  }, [isAuthenticated, navigate])

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <CheckoutStepper currentStep="customer" isAuthenticated={isAuthenticated} />
          <h1 className="text-2xl font-bold text-center text-gray-900">
            Datos del Cliente
          </h1>
        </div>

        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="bg-white shadow-md rounded-lg p-8 space-y-4">
            <TextField
              label="Email"
              name="email"
              type="email"
              register={register}
              validation={{
                required: 'El email es requerido',
                validate: validateEmail,
              }}
              error={errors.email?.message}
              placeholder="Ingresa tu email"
              disabled={isAuthenticated && !!user?.email}
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <TextField
                label="Nombre"
                name="first_name"
                type="text"
                register={register}
                validation={{
                  required: 'El nombre es requerido',
                  validate: validateOnlyLetters,
                }}
                error={errors.first_name?.message}
                placeholder="Ingresa tu nombre"
              />

              <TextField
                label="Apellido"
                name="last_name"
                type="text"
                register={register}
                validation={{
                  required: 'El apellido es requerido',
                  validate: validateOnlyLetters,
                }}
                error={errors.last_name?.message}
                placeholder="Ingresa tu apellido"
              />
            </div>

            <TextField
              label="Teléfono"
              name="phone"
              type="tel"
              register={register}
              validation={{
                required: 'El teléfono es requerido',
                validate: validateChileanPhone,
              }}
              error={errors.phone?.message}
              placeholder="Ej: +569 12345678"
              helperText="Formato: +569 + 8 dígitos"
            />

            <div className="flex gap-4 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/cart')}
                fullWidth
              >
                Volver al Carrito
              </Button>
              <Button type="submit" fullWidth>
                Continuar
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}

export default StepCustomer





