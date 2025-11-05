import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import Button from '../../components/common/Button'
import TextField from '../../components/forms/TextField'
import Spinner from '../../components/common/Spinner'
import { validateEmail } from '../../utils/validations'
import { authService } from '../../services/auth'

const ForgotPassword = () => {
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm()

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      await authService.requestPasswordReset(data.email)
      setSubmitted(true)
    } catch (error) {
      // No mostrar error para evitar confirmar si un email existe o no
      // Siempre mostrar el mensaje de éxito
      setSubmitted(true)
      console.error('Error requesting password reset:', error)
    } finally {
      setLoading(false)
    }
  }

  if (submitted) {
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
                  Si el email existe, recibirás instrucciones para restablecer tu contraseña.
                </p>
              </div>
            </div>
            <div className="text-center">
              <Link to="/login">
                <Button variant="outline" fullWidth>
                  Volver al Login
                </Button>
              </Link>
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
            Recuperar Contraseña
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Ingresa tu email y te enviaremos un enlace para restablecer tu contraseña
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
              error={errors.email?.message}
              placeholder="Ingresa tu email"
              autoComplete="email"
            />

            <Button
              type="submit"
              fullWidth
              size="lg"
              disabled={loading}
            >
              {loading ? <Spinner size="sm" /> : 'Enviar Enlace'}
            </Button>

            <div className="text-center">
              <Link 
                to="/login" 
                className="text-sm text-primary-600 hover:text-primary-500"
              >
                Volver al Login
              </Link>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}

export default ForgotPassword

