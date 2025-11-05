import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import Button from '../components/common/Button'
import TextField from '../components/forms/TextField'
import Spinner from '../components/common/Spinner'
import { authService } from '../services/auth'
import { useAuthStore } from '../store/authSlice'
import { useToast } from '../components/common/Toast'
import { validateName, validateChileanPhone, validatePostalCode } from '../utils/validations'
import apiClient from '../services/apiClient'

const Profile = () => {
  const navigate = useNavigate()
  const { user, updateUser, logout } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [loadingProfile, setLoadingProfile] = useState(true)
  const [hasChanges, setHasChanges] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const toast = useToast()
  
  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    setValue,
    reset,
    watch,
  } = useForm()
  
  const watchedValues = watch()

  useEffect(() => {
    loadProfile()
  }, [])

  useEffect(() => {
    if (user) {
      reset({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        phone: user.phone || '',
        street: user.street || '',
        city: user.city || '',
        region: user.region || '',
        postal_code: user.postal_code || '',
      })
    }
  }, [user, reset])

  useEffect(() => {
    setHasChanges(isDirty)
  }, [isDirty, watchedValues])

  const loadProfile = async () => {
    setLoadingProfile(true)
    try {
      const profileData = await authService.getProfile()
      updateUser(profileData)
    } catch (error) {
      toast.error('Error al cargar el perfil')
      console.error('Error loading profile:', error)
    } finally {
      setLoadingProfile(false)
    }
  }

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      const updatedProfile = await authService.updateProfile(data)
      updateUser(updatedProfile)
      reset(data)
      toast.success('Perfil actualizado exitosamente')
      setHasChanges(false)
    } catch (error) {
      toast.error(error.response?.data?.error || 'Error al actualizar el perfil')
      console.error('Error updating profile:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDiscard = () => {
    if (user) {
      reset({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        phone: user.phone || '',
        street: user.street || '',
        city: user.city || '',
        region: user.region || '',
        postal_code: user.postal_code || '',
      })
      setHasChanges(false)
    }
  }

  const handleDeleteAccount = async () => {
    if (!showDeleteConfirm) {
      setShowDeleteConfirm(true)
      return
    }

    setDeleting(true)
    try {
      await apiClient.delete('/users/me')
      logout()
      toast.success('Tu cuenta ha sido eliminada')
      navigate('/')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Error al eliminar la cuenta')
      console.error('Error deleting account:', error)
      setShowDeleteConfirm(false)
    } finally {
      setDeleting(false)
    }
  }

  if (loadingProfile) {
    return (
      <div className="min-h-screen flex justify-center items-center">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Mi Perfil</h1>

        {hasChanges && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-start">
              <svg className="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <p className="text-sm text-blue-800">
                Tienes cambios sin guardar. Recuerda guardar antes de salir.
              </p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="bg-white shadow-md rounded-lg p-8 space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Información Personal</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <TextField
                  label="Nombre"
                  name="first_name"
                  register={register}
                  validation={{
                    required: 'El nombre es requerido',
                    validate: validateName,
                  }}
                  error={errors.first_name?.message}
                />

                <TextField
                  label="Apellido"
                  name="last_name"
                  register={register}
                  validation={{
                    required: 'El apellido es requerido',
                    validate: validateName,
                  }}
                  error={errors.last_name?.message}
                />
              </div>

              <TextField
                label="Email"
                name="email"
                type="email"
                register={register}
                validation={{
                  required: 'El email es requerido',
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: 'Email inválido',
                  },
                }}
                error={errors.email?.message}
                disabled
              />

              <TextField
                label="Teléfono"
                name="phone"
                type="tel"
                register={register}
                validation={{
                  validate: validateChileanPhone,
                }}
                error={errors.phone?.message}
                placeholder="+56912345678"
                helperText="Formato: +569 + 8 dígitos"
              />
            </div>

            <div className="border-t pt-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Dirección</h2>
              
              <TextField
                label="Calle y Número"
                name="street"
                register={register}
                error={errors.street?.message}
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <TextField
                  label="Ciudad"
                  name="city"
                  register={register}
                  error={errors.city?.message}
                />

                <TextField
                  label="Región"
                  name="region"
                  register={register}
                  error={errors.region?.message}
                />
              </div>

              <TextField
                label="Código Postal"
                name="postal_code"
                register={register}
                validation={{
                  validate: validatePostalCode,
                }}
                error={errors.postal_code?.message}
              />
            </div>

            <div className="pt-4 space-y-3">
              <div className="flex gap-3">
                <Button
                  type="submit"
                  disabled={loading || !hasChanges}
                  size="lg"
                  className="flex-1"
                >
                  {loading ? <Spinner size="sm" /> : 'Guardar Cambios'}
                </Button>
                {hasChanges && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleDiscard}
                    disabled={loading}
                    size="lg"
                  >
                    Descartar
                  </Button>
                )}
              </div>

              <div className="border-t pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleDeleteAccount}
                  disabled={deleting}
                  size="lg"
                  className="w-full text-red-600 border-red-300 hover:bg-red-50"
                >
                  {deleting ? (
                    <Spinner size="sm" />
                  ) : showDeleteConfirm ? (
                    'Confirmar Eliminación'
                  ) : (
                    'Eliminar Cuenta'
                  )}
                </Button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Profile





