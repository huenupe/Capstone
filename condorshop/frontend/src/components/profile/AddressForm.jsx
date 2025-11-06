import { useForm } from 'react-hook-form'
import Button from '../common/Button'
import TextField from '../forms/TextField'
import Select from '../forms/Select'
import { validatePostalCode } from '../../utils/validations'

const AddressForm = ({ address, regions, onSave, onCancel }) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
  } = useForm({
    defaultValues: address ? {
      label: address.label || '',
      street: address.street || '',
      number: address.number || '',
      apartment: address.apartment || '',
      city: address.city || '',
      region: regions.find(r => 
        r.label.toLowerCase().includes(address.region?.toLowerCase()) ||
        address.region?.toLowerCase().includes(r.value)
      )?.value || address.region || '',
      postal_code: address.postal_code || '',
      is_default: address.is_default || false,
    } : {
      label: '',
      street: '',
      number: '',
      apartment: '',
      city: '',
      region: '',
      postal_code: '',
      is_default: false,
    },
  })

  const onSubmit = async (data) => {
    // Verificar que no haya errores de validación
    if (Object.keys(errors).length > 0) {
      return
    }
    
    // Validar campos requeridos manualmente
    if (!data.street || !data.street.trim()) {
      return
    }
    if (!data.city || !data.city.trim()) {
      return
    }
    if (!data.region) {
      return
    }
    if (!data.postal_code || !data.postal_code.trim()) {
      return
    }
    
    // Mapear región del frontend al formato del backend
    const regionObj = regions.find(r => r.value === data.region)
    const regionLabel = regionObj?.label || data.region
    
    if (!regionLabel) {
      return
    }
    
    // Preparar datos para enviar al backend
    const addressData = {
      street: data.street.trim(),
      city: data.city.trim(),
      region: regionLabel,
      postal_code: data.postal_code.trim(),
      is_default: data.is_default || false,
    }
    
    // Agregar campos opcionales solo si tienen valor
    if (data.number && data.number.trim()) {
      addressData.number = data.number.trim()
    }
    if (data.apartment && data.apartment.trim()) {
      addressData.apartment = data.apartment.trim()
    }
    if (data.label && data.label.trim()) {
      addressData.label = data.label.trim()
    }
    
    try {
      await onSave(addressData)
    } catch (error) {
      // Error manejado por el componente padre
    }
  }

  return (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 mt-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        {address ? 'Editar Dirección' : 'Nueva Dirección'}
      </h3>
      
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <TextField
          label="Etiqueta (opcional)"
          name="label"
          register={register}
          error={errors.label?.message}
          placeholder="Ej: Casa, Oficina, etc."
          helperText="Un nombre para identificar esta dirección"
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Select
            label="Región"
            name="region"
            register={register}
            validation={{
              required: 'La región es requerida',
            }}
            error={errors.region?.message}
            options={regions}
            placeholder="Selecciona una región"
          />

          <TextField
            label="Comuna"
            name="city"
            type="text"
            register={register}
            validation={{
              required: 'La comuna es requerida',
            }}
            error={errors.city?.message}
            placeholder="Selecciona una comuna"
          />
        </div>

        <TextField
          label="Calle"
          name="street"
          type="text"
          register={register}
          validation={{
            required: 'La calle es requerida',
          }}
          error={errors.street?.message}
          placeholder="Ingresa el nombre de la calle"
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TextField
            label="Número"
            name="number"
            type="text"
            register={register}
            error={errors.number?.message}
            placeholder="Ingresa el número de la calle (opcional)"
          />

          <TextField
            label="Dpto/Casa/Oficina"
            name="apartment"
            type="text"
            register={register}
            error={errors.apartment?.message}
            placeholder="Opcional"
          />
        </div>

        <TextField
          label="Código Postal"
          name="postal_code"
          type="text"
          register={register}
          validation={{
            required: 'El código postal es requerido',
            validate: (value) => {
              if (!value || value.trim() === '') {
                return 'El código postal es requerido'
              }
              return validatePostalCode(value)
            },
          }}
          error={errors.postal_code?.message}
          placeholder="1234567"
        />

        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="is_default"
            {...register('is_default')}
            className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
          />
          <label htmlFor="is_default" className="text-sm text-gray-700 cursor-pointer">
            Marcar como dirección predeterminada
          </label>
        </div>

        <div className="flex gap-3 pt-2">
          <Button type="submit" className="flex-1">
            {address ? 'Actualizar Dirección' : 'Guardar Dirección'}
          </Button>
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancelar
          </Button>
        </div>
      </form>
    </div>
  )
}

export default AddressForm

