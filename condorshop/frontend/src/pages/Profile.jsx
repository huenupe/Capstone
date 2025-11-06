import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import Button from '../components/common/Button'
import TextField from '../components/forms/TextField'
import Select from '../components/forms/Select'
import Spinner from '../components/common/Spinner'
import { authService } from '../services/auth'
import { usersService } from '../services/users'
import { useAuthStore } from '../store/authSlice'
import { useToast } from '../components/common/Toast'
import { validateName, validateChileanPhone, validatePostalCode } from '../utils/validations'
import AddressForm from '../components/profile/AddressForm'
import apiClient from '../services/apiClient'
import { REGIONS } from '../constants/regions'

const Profile = () => {
  const navigate = useNavigate()
  const { user, updateUser, logout } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [loadingProfile, setLoadingProfile] = useState(true)
  const [hasChanges, setHasChanges] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [savedAddresses, setSavedAddresses] = useState([])
  const [loadingAddresses, setLoadingAddresses] = useState(false)
  const [editingAddressId, setEditingAddressId] = useState(null)
  const [showAddressForm, setShowAddressForm] = useState(false)
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
      })
    }
  }, [user, reset])

  useEffect(() => {
    loadSavedAddresses()
  }, [])

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

  const loadSavedAddresses = async () => {
    setLoadingAddresses(true)
    try {
      const addresses = await usersService.getAddresses()
      setSavedAddresses(addresses || [])
    } catch (error) {
      console.error('Error loading saved addresses:', error)
    } finally {
      setLoadingAddresses(false)
    }
  }

  const handleEditAddress = (address) => {
    setEditingAddressId(address.id)
    setShowAddressForm(true)
    // Los campos se llenarán en el formulario de dirección
  }

  const handleDeleteAddress = async (addressId) => {
    if (!window.confirm('¿Estás seguro de que quieres eliminar esta dirección?')) {
      return
    }
    try {
      await usersService.deleteAddress(addressId)
      toast.success('Dirección eliminada exitosamente')
      loadSavedAddresses()
    } catch (error) {
      toast.error('Error al eliminar la dirección')
      console.error('Error deleting address:', error)
    }
  }

  const handleSetDefaultAddress = async (addressId) => {
    try {
      await usersService.updateAddress(addressId, { is_default: true })
      toast.success('Dirección predeterminada actualizada')
      loadSavedAddresses()
    } catch (error) {
      toast.error('Error al actualizar la dirección predeterminada')
      console.error('Error setting default address:', error)
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

            <div className="pt-4 space-y-3">
              <div className="flex gap-3">
                <Button
                  type="submit"
                  disabled={loading || !hasChanges || showAddressForm}
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
                    disabled={loading || showAddressForm}
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

        {/* Sección de Direcciones - Fuera del formulario principal para evitar anidamiento de forms */}
        <div className="bg-white shadow-md rounded-lg p-8 mt-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Direcciones Guardadas</h2>
              
              {loadingAddresses ? (
                <div className="flex justify-center py-4">
                  <Spinner size="sm" />
                </div>
              ) : savedAddresses.length > 0 ? (
                <div className="space-y-3 mb-4">
                  {savedAddresses.map((address) => (
                    <div
                      key={address.id}
                      className={`border rounded-lg p-4 ${
                        address.is_default ? 'border-primary-600 bg-primary-50' : 'border-gray-200'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          {address.is_default && (
                            <span className="inline-block bg-primary-600 text-white text-xs px-2 py-1 rounded mb-2">
                              Predeterminada
                            </span>
                          )}
                          {address.label && (
                            <h3 className="font-semibold text-gray-900 mb-1">{address.label}</h3>
                          )}
                          <p className="text-sm text-gray-700">
                            {address.street} {address.number ? address.number : ''}
                            {address.apartment ? `, Dpto ${address.apartment}` : ''}
                          </p>
                          <p className="text-sm text-gray-600">
                            {address.city}, {address.region}
                          </p>
                          {address.postal_code && (
                            <p className="text-xs text-gray-500">
                              Código Postal: {address.postal_code}
                            </p>
                          )}
                        </div>
                        <div className="flex gap-2 ml-4">
                          {!address.is_default && (
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={() => handleSetDefaultAddress(address.id)}
                            >
                              Predeterminada
                            </Button>
                          )}
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => handleEditAddress(address)}
                          >
                            Editar
                          </Button>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => handleDeleteAddress(address.id)}
                            className="text-red-600 border-red-300 hover:bg-red-50"
                          >
                            Eliminar
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm mb-4">
                  No tienes direcciones guardadas. Agrega una nueva dirección a continuación.
                </p>
              )}

              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setEditingAddressId(null)
                  setShowAddressForm(!showAddressForm)
                }}
                className="mb-4"
              >
                {showAddressForm ? 'Cancelar' : editingAddressId ? 'Cancelar Edición' : 'Agregar Nueva Dirección'}
              </Button>

              {showAddressForm && (
                <AddressForm
                  address={editingAddressId ? savedAddresses.find(a => a.id === editingAddressId) : null}
              regions={REGIONS}
                  onSave={async (addressData) => {
                    try {
                      // Validar que tenemos los datos mínimos
                      if (!addressData.street || !addressData.city || !addressData.region || !addressData.postal_code) {
                        toast.error('Por favor completa todos los campos requeridos')
                        return
                      }
                      
                      if (editingAddressId) {
                        await usersService.updateAddress(editingAddressId, addressData)
                        toast.success('Dirección actualizada exitosamente')
                        setShowAddressForm(false)
                        setEditingAddressId(null)
                        await loadSavedAddresses()
                      } else {
                        await usersService.createAddress(addressData)
                        toast.success('Dirección guardada exitosamente')
                        setShowAddressForm(false)
                        setEditingAddressId(null)
                        await loadSavedAddresses()
                      }
                    } catch (error) {
                      let errorMessage = 'Error al guardar la dirección'
                      
                      if (error.response?.data) {
                        if (typeof error.response.data === 'string') {
                          errorMessage = error.response.data
                        } else if (error.response.data.error) {
                          errorMessage = error.response.data.error
                        } else if (error.response.data.message) {
                          errorMessage = error.response.data.message
                        } else if (typeof error.response.data === 'object') {
                          // Si hay errores de validación, mostrar el primero
                          const firstError = Object.values(error.response.data)[0]
                          if (Array.isArray(firstError)) {
                            errorMessage = firstError[0]
                          } else if (typeof firstError === 'string') {
                            errorMessage = firstError
                          }
                        }
                      } else if (error.message) {
                        errorMessage = error.message
                      }
                      
                      toast.error(errorMessage)
                      throw error // Re-lanzar para que el formulario sepa que hubo un error
                    }
                  }}
                  onCancel={() => {
                    setShowAddressForm(false)
                    setEditingAddressId(null)
                  }}
                />
              )}
        </div>
      </div>
    </div>
  )
}

export default Profile





