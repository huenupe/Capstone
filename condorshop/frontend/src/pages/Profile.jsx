import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import Button from '../components/common/Button'
import TextField from '../components/forms/TextField'
import Spinner from '../components/common/Spinner'
import { authService } from '../services/auth'
import { useAuthStore } from '../store/authSlice'
import { useToast } from '../components/common/Toast'

const Profile = () => {
  const { user, updateUser } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [loadingProfile, setLoadingProfile] = useState(true)
  const toast = useToast()
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
  } = useForm()

  useEffect(() => {
    loadProfile()
  }, [])

  useEffect(() => {
    if (user) {
      setValue('first_name', user.first_name || '')
      setValue('last_name', user.last_name || '')
      setValue('email', user.email || '')
      setValue('phone', user.phone || '')
      setValue('street', user.street || '')
      setValue('city', user.city || '')
      setValue('region', user.region || '')
      setValue('postal_code', user.postal_code || '')
    }
  }, [user, setValue])

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
      toast.success('Perfil actualizado exitosamente')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Error al actualizar el perfil')
      console.error('Error updating profile:', error)
    } finally {
      setLoading(false)
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

        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="bg-white shadow-md rounded-lg p-8 space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Información Personal</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <TextField
                  label="Nombre"
                  name="first_name"
                  register={register}
                  validation={{ required: 'El nombre es requerido' }}
                  error={errors.first_name?.message}
                />

                <TextField
                  label="Apellido"
                  name="last_name"
                  register={register}
                  validation={{ required: 'El apellido es requerido' }}
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
                error={errors.phone?.message}
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
                error={errors.postal_code?.message}
              />
            </div>

            <div className="pt-4">
              <Button type="submit" disabled={loading} size="lg" fullWidth>
                {loading ? <Spinner size="sm" /> : 'Guardar Cambios'}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Profile





