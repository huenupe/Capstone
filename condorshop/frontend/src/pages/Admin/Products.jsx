import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { formatPrice } from '../../utils/formatPrice'
import Button from '../../components/common/Button'
import TextField from '../../components/forms/TextField'
import Select from '../../components/forms/Select'
import Modal from '../../components/common/Modal'
import Spinner from '../../components/common/Spinner'
import { adminService } from '../../services/admin'
import { productsService } from '../../services/products'
import { useToast } from '../../components/common/Toast'

const Products = () => {
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState(null)
  const [deletingProduct, setDeletingProduct] = useState(null)
  const [search, setSearch] = useState('')
  const toast = useToast()

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
  } = useForm()

  useEffect(() => {
    loadProducts()
    loadCategories()
  }, [])

  const loadProducts = async () => {
    setLoading(true)
    try {
      const data = await adminService.getProducts({ search, page_size: 100 })
      setProducts(Array.isArray(data) ? data : data.results || [])
    } catch (error) {
      toast.error('Error al cargar productos')
      console.error('Error loading products:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadCategories = async () => {
    try {
      const data = await productsService.getCategories()
      setCategories(Array.isArray(data) ? data : data.results || [])
    } catch (error) {
      console.error('Error loading categories:', error)
    }
  }

  useEffect(() => {
    loadProducts()
  }, [search])

  const handleCreate = () => {
    setEditingProduct(null)
    reset()
    setModalOpen(true)
  }

  const handleEdit = (product) => {
    setEditingProduct(product)
    setValue('name', product.name || '')
    setValue('description', product.description || '')
    setValue('price', product.price || '')
    setValue('stock_qty', product.stock_qty || '')
    setValue('category', product.category?.id || '')
    setValue('active', product.active || false)
    setModalOpen(true)
  }

  const handleDelete = async (productId) => {
    if (!confirm('¿Estás seguro de eliminar este producto?')) return

    setDeletingProduct(productId)
    try {
      await adminService.deleteProduct(productId)
      toast.success('Producto eliminado')
      loadProducts()
    } catch (error) {
      toast.error('Error al eliminar producto')
      console.error('Error deleting product:', error)
    } finally {
      setDeletingProduct(null)
    }
  }

  const onSubmit = async (data) => {
    const formData = new FormData()
    
    Object.keys(data).forEach((key) => {
      if (key === 'images') {
        // Handle multiple images
        Array.from(data[key]).forEach((file) => {
          formData.append('images', file)
        })
      } else if (data[key] !== null && data[key] !== undefined && data[key] !== '') {
        formData.append(key, data[key])
      }
    })

    try {
      if (editingProduct) {
        await adminService.updateProduct(editingProduct.id, formData)
        toast.success('Producto actualizado')
      } else {
        await adminService.createProduct(formData)
        toast.success('Producto creado')
      }
      setModalOpen(false)
      reset()
      loadProducts()
    } catch (error) {
      toast.error(error.response?.data?.error || 'Error al guardar producto')
      console.error('Error saving product:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Gestionar Productos</h1>
          <Button onClick={handleCreate}>Nuevo Producto</Button>
        </div>

        <div className="mb-6">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar productos..."
            className="w-full max-w-md px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Spinner size="lg" />
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Imagen
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Nombre
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Precio
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Stock
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Estado
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {products.map((product) => (
                  <tr key={product.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <img
                        src={product.images?.[0]?.image || '/placeholder-product.jpg'}
                        alt={product.name}
                        className="w-16 h-16 object-cover rounded"
                      />
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">{product.name}</div>
                      <div className="text-sm text-gray-500">{product.category?.name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatPrice(product.price)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {product.stock_qty}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          product.active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {product.active ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEdit(product)}
                      >
                        Editar
                      </Button>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => handleDelete(product.id)}
                        disabled={deletingProduct === product.id}
                      >
                        Eliminar
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Create/Edit Modal */}
        <Modal
          isOpen={modalOpen}
          onClose={() => {
            setModalOpen(false)
            reset()
          }}
          title={editingProduct ? 'Editar Producto' : 'Nuevo Producto'}
          size="lg"
          footer={
            <div className="flex gap-4">
              <Button
                variant="outline"
                onClick={() => {
                  setModalOpen(false)
                  reset()
                }}
              >
                Cancelar
              </Button>
              <Button onClick={handleSubmit(onSubmit)}>Guardar</Button>
            </div>
          }
        >
          <form className="space-y-4">
            <TextField
              label="Nombre"
              name="name"
              register={register}
              validation={{ required: 'El nombre es requerido' }}
              error={errors.name?.message}
            />

            <TextField
              label="Descripción"
              name="description"
              type="textarea"
              register={register}
              validation={{ required: 'La descripción es requerida' }}
              error={errors.description?.message}
            />

            <div className="grid grid-cols-2 gap-4">
              <TextField
                label="Precio"
                name="price"
                type="number"
                register={register}
                validation={{
                  required: 'El precio es requerido',
                  min: { value: 0, message: 'El precio debe ser mayor a 0' },
                }}
                error={errors.price?.message}
              />

              <TextField
                label="Stock"
                name="stock_qty"
                type="number"
                register={register}
                validation={{
                  required: 'El stock es requerido',
                  min: { value: 0, message: 'El stock debe ser mayor o igual a 0' },
                }}
                error={errors.stock_qty?.message}
              />
            </div>

            <Select
              label="Categoría"
              name="category"
              register={register}
              options={categories.map((cat) => ({
                value: cat.id,
                label: cat.name,
              }))}
              error={errors.category?.message}
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <input
                  type="checkbox"
                  {...register('active')}
                  className="mr-2"
                />
                Producto activo
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Imágenes
              </label>
              <input
                type="file"
                multiple
                accept="image/*"
                {...register('images')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
          </form>
        </Modal>
      </div>
    </div>
  )
}

export default Products





