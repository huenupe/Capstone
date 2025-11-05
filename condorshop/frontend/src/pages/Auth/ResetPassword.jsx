import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import Button from '../../components/common/Button'
import TextField from '../../components/forms/TextField'
import Spinner from '../../components/common/Spinner'
import { validatePassword } from '../../utils/validations'

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
      // TODO: Implementar llamada al backend cuando esté listo
      // await authService.resetPassword({ token, password: data.password })
      
      // Simular delay para UX
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setSuccess(true)
      
      // Redirigir después de 2 segundos
      setTimeout(() => {
        navigate('/login')
      }, 2000)
    } catch (error) {
      console.error('Error resetting password:', error)
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div className="bg-white shadow-md rounded-lg px-8 pt-6 pb-8 text-center">
            <div className="mb-6">
              <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Contraseña Actualizada
              </h2>
              <p className="text-gray-600">
                Tu contraseña ha sido actualizada exitosamente. Redirigiendo al login...
              </p>
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
                validate: (value) =>
                  value === password || 'Las contraseñas no coinciden',
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

