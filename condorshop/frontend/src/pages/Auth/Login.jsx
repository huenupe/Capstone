import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import Button from '../../components/common/Button'
import TextField from '../../components/forms/TextField'
import Spinner from '../../components/common/Spinner'
import { authService } from '../../services/auth'
import { useAuthStore } from '../../store/authSlice'
import { useCartStore } from '../../store/cartSlice'
import { cartService } from '../../services/cart'
import { validateEmail } from '../../utils/validations'

const Login = () => {
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const { setCart } = useCartStore()
  const [loading, setLoading] = useState(false)
  const [emailError, setEmailError] = useState('')
  const [passwordError, setPasswordError] = useState('')
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm()

  const onSubmit = async (data) => {
    // Limpiar errores previos
    setEmailError('')
    setPasswordError('')
    
    setLoading(true)
    try {
      const { user, token } = await authService.login(data)
      login(user, token)
      
      // ✅ CORRECCIÓN: Sincronizar carrito después de iniciar sesión
      // Esto asegura que el carrito del usuario autenticado se cargue correctamente
      // y no se pierdan productos al iniciar sesión
      try {
        const cartData = await cartService.getCart()
        setCart(cartData)
      } catch (cartError) {
        // No bloquear el login si hay error al cargar el carrito
        console.error('Error loading cart after login:', cartError)
      }
      
      navigate('/')
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Error al iniciar sesión'
      
      // Determinar si es error de email o contraseña
      if (errorMessage.toLowerCase().includes('email') || errorMessage.toLowerCase().includes('no existe')) {
        setEmailError('Email incorrecto')
        setError('email', { type: 'manual', message: 'Email incorrecto' })
      } else if (errorMessage.toLowerCase().includes('contraseña') || errorMessage.toLowerCase().includes('password') || errorMessage.toLowerCase().includes('credenciales')) {
        setPasswordError('Contraseña incorrecta')
        setError('password', { type: 'manual', message: 'Contraseña incorrecta' })
      } else {
        // Error genérico - mostrar en ambos campos o en email
        setEmailError(errorMessage)
        setError('email', { type: 'manual', message: errorMessage })
      }
      console.error('Error logging in:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Iniciar Sesión
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            ¿No tienes una cuenta?{' '}
            <Link to="/register" className="font-medium text-primary-600 hover:text-primary-500">
              Regístrate aquí
            </Link>
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="bg-white shadow-md rounded-lg px-8 pt-6 pb-8 space-y-4">
            <TextField
              label="Email"
              name="email"
              type="email"
              register={register}
              validation={{
                required: 'El email es requerido',
                validate: validateEmail,
              }}
              error={errors.email?.message || emailError}
              placeholder="Ingresa tu email"
              autoComplete="email"
            />

            <TextField
              label="Contraseña"
              name="password"
              type="password"
              register={register}
              validation={{
                required: 'La contraseña es requerida',
              }}
              error={errors.password?.message || passwordError}
              placeholder="Ingresa tu contraseña"
              autoComplete="current-password"
            />

            <div className="text-right">
              <Link 
                to="/forgot-password" 
                className="text-sm text-primary-600 hover:text-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded"
              >
                ¿Olvidaste tu contraseña?
              </Link>
            </div>

            <Button
              type="submit"
              fullWidth
              size="lg"
              disabled={loading}
            >
              {loading ? <Spinner size="sm" /> : 'Iniciar Sesión'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Login





