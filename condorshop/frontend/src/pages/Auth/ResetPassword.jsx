import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import Button from '../../components/common/Button'
import TextField from '../../components/forms/TextField'
import Spinner from '../../components/common/Spinner'
import { validatePassword, validatePasswordMatch } from '../../utils/validations'
import { authService } from '../../services/auth'

const ResetPassword = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const token = searchParams.get('token')
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm()

  const password = watch('password')

  useEffect(() => {
    if (!token) {
      navigate('/forgot-password')
    }
  }, [token, navigate])

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      await authService.confirmPasswordReset({
        token,
        new_password: data.password,
      })
      
      setSuccess(true)
      
      // Redirigir después de 2 segundos
      setTimeout(() => {
        navigate('/login')
      }, 2000)
    } catch (error) {
      console.error('Error resetting password:', error)
      // El error se mostrará en el formulario si es de validación
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div className="bg-white shadow-md rounded-lg px-8 pt-6 pb-8">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <div className="flex items-start">
                <svg className="w-5 h-5 text-green-600 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <p className="text-sm text-green-800">
                  Tu contraseña ha sido actualizada exitosamente. Redirigiendo al login...
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Nueva Contraseña
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Ingresa tu nueva contraseña
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="bg-white shadow-md rounded-lg px-8 pt-6 pb-8 space-y-4">
            <TextField
              label="Nueva Contraseña"
              name="password"
              type="password"
              register={register}
              validation={{
                required: 'La contraseña es requerida',
                validate: validatePassword,
              }}
              error={errors.password?.message}
              placeholder="Ingresa tu nueva contraseña"
              autoComplete="new-password"
            />

            <TextField
              label="Confirmar Contraseña"
              name="confirmPassword"
              type="password"
              register={register}
              validation={{
                required: 'Confirma tu contraseña',
                validate: validatePasswordMatch(password),
              }}
              error={errors.confirmPassword?.message}
              placeholder="Confirma tu nueva contraseña"
              autoComplete="new-password"
            />

            <Button
              type="submit"
              fullWidth
              size="lg"
              disabled={loading}
            >
              {loading ? <Spinner size="sm" /> : 'Actualizar'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default ResetPassword

