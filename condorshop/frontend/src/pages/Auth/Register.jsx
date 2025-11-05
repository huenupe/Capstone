import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import Button from '../../components/common/Button'
import TextField from '../../components/forms/TextField'
import Spinner from '../../components/common/Spinner'
import { authService } from '../../services/auth'
import { useAuthStore } from '../../store/authSlice'
import { useToast } from '../../components/common/Toast'
import { validateEmail, validateOnlyLetters, validateChileanPhone, validatePassword } from '../../utils/validations'

const Register = () => {
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const toast = useToast()
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm()

  const password = watch('password')

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      // Convertir confirmPassword a password_confirm para el backend
      const registrationData = {
        email: data.email,
        first_name: data.first_name,
        last_name: data.last_name,
        password: data.password,
        password_confirm: data.confirmPassword,
      }
      
      const { user, token } = await authService.register(registrationData)
      login(user, token)
      
      toast.success('¡Registro exitoso!')
      navigate('/')
    } catch (error) {
      // Mejorar manejo de errores para mostrar mensajes específicos
      const errorData = error.response?.data
      let errorMessage = 'Error al registrar usuario'
      
      if (errorData) {
        // Si hay errores de validación del serializer, priorizar mensajes específicos
        if (errorData.password_confirm) {
          errorMessage = Array.isArray(errorData.password_confirm) 
            ? errorData.password_confirm[0] 
            : errorData.password_confirm
        } else if (errorData.password) {
          errorMessage = Array.isArray(errorData.password) 
            ? errorData.password[0] 
            : errorData.password
        } else if (errorData.email) {
          errorMessage = Array.isArray(errorData.email) 
            ? errorData.email[0] 
            : errorData.email
        } else if (errorData.first_name) {
          errorMessage = Array.isArray(errorData.first_name) 
            ? errorData.first_name[0] 
            : errorData.first_name
        } else if (errorData.last_name) {
          errorMessage = Array.isArray(errorData.last_name) 
            ? errorData.last_name[0] 
            : errorData.last_name
        } else if (errorData.non_field_errors) {
          errorMessage = Array.isArray(errorData.non_field_errors) 
            ? errorData.non_field_errors[0] 
            : errorData.non_field_errors
        } else if (errorData.error) {
          errorMessage = errorData.error
        } else if (typeof errorData === 'object') {
          // Si hay múltiples errores, mostrar el primero
          const firstError = Object.values(errorData)[0]
          errorMessage = Array.isArray(firstError) ? firstError[0] : firstError
        }
      }
      
      toast.error(errorMessage)
      console.error('Error registering:', error.response?.data || error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Crear Cuenta
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            ¿Ya tienes una cuenta?{' '}
            <Link to="/login" className="font-medium text-primary-600 hover:text-primary-500">
              Inicia sesión aquí
            </Link>
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="bg-white shadow-md rounded-lg px-8 pt-6 pb-8 space-y-4">
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
                autoComplete="given-name"
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
                autoComplete="family-name"
              />
            </div>

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
              autoComplete="email"
            />

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
              autoComplete="tel"
            />

            <TextField
              label="Contraseña"
              name="password"
              type="password"
              register={register}
              validation={{
                required: 'La contraseña es requerida',
                validate: validatePassword,
              }}
              error={errors.password?.message}
              placeholder="Ingresa tu contraseña"
              autoComplete="new-password"
            />

            <TextField
              label="Confirmar Contraseña"
              name="confirmPassword"
              type="password"
              register={register}
              validation={{
                required: 'Confirma tu contraseña',
                validate: (value) =>
                  value === password || 'Las contraseñas no coinciden',
              }}
              error={errors.confirmPassword?.message}
              placeholder="Confirma tu contraseña"
              autoComplete="new-password"
            />

            <Button
              type="submit"
              fullWidth
              size="lg"
              disabled={loading}
            >
              {loading ? <Spinner size="sm" /> : 'Registrarse'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Register





