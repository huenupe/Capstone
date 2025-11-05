import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import Button from '../../components/common/Button'
import TextField from '../../components/forms/TextField'
import Spinner from '../../components/common/Spinner'
import { validateEmail } from '../../utils/validations'

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
      // TODO: Implementar llamada al backend cuando esté listo
      // await authService.requestPasswordReset(data.email)
      
      // Simular delay para UX
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setSubmitted(true)
    } catch (error) {
      console.error('Error requesting password reset:', error)
      // No mostrar error para evitar confirmar si un email existe o no
    } finally {
      setLoading(false)
    }
  }

  if (submitted) {
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
                Correo Enviado
              </h2>
              <p className="text-gray-600">
                Te enviamos un correo con el enlace para restablecer tu contraseña si el email existe.
              </p>
            </div>
            <Link to="/login">
              <Button variant="outline" fullWidth>
                Volver al Login
              </Button>
            </Link>
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

