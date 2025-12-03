import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { useParams, Link, useSearchParams } from 'react-router-dom'
import { getProductImage } from '../utils/getProductImage'
import Button from '../components/common/Button'
import Spinner from '../components/common/Spinner'
import PriceTag from '../components/products/PriceTag'
import QuantityStepper from '../components/forms/QuantityStepper'
import { productsService } from '../services/products'
import { categoriesService } from '../services/categories'
import { cartService } from '../services/cart'
import { useCartStore } from '../store/cartSlice'
import { useToast } from '../components/common/Toast'

// Product card with cart functionality for CategoryPage
const ProductCardWithCart = ({ product, onAddToCart }) => {
  const [quantity, setQuantity] = useState(1)

  const handleAddToCartClick = () => {
    // ✅ CRÍTICO: Pasar la cantidad ACTUAL del estado, no un valor fijo
    const currentQuantity = quantity
    onAddToCart(product, currentQuantity)
    // ✅ MEJORA: Resetear stepper a 1 después de agregar
    setQuantity(1)
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-shadow">
      <Link to={`/product/${product.slug}`} className="block">
        <img
          src={getProductImage(product)}
          alt={product.name}
          className="w-full h-48 object-cover"
          onError={(e) => {
            e.target.src = '/placeholder-product.jpg'
          }}
        />
        <div className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
            {product.name}
          </h3>
          <PriceTag
            price={product.final_price || product.price}
            originalPrice={product.has_discount ? product.price : null}
            discountPercent={product.has_discount ? (product.calculated_discount_percent || product.discount_percent) : null}
            size="md"
          />
        </div>
      </Link>
      <div className="px-4 pb-4 space-y-3">
        {product.stock_qty > 0 && (
          <QuantityStepper
            value={quantity}
            onChange={setQuantity}
            min={1}
            max={Math.min(product.stock_qty, 10)}
          />
        )}
        <Button
          onClick={handleAddToCartClick}
          disabled={product.stock_qty === 0}
          fullWidth
          className="focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          {product.stock_qty === 0 ? 'Sin Stock' : 'Agregar al carrito'}
        </Button>
      </div>
    </div>
  )
}

const CategoryPage = () => {
  const { slug } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const querySyncRef = useRef(searchParams.toString())
  const [category, setCategory] = useState(null)
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [pagination, setPagination] = useState({})
  const toast = useToast()
  const toastRef = useRef(toast)

  // Filters
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [minPrice, setMinPrice] = useState(searchParams.get('min_price') ?? '')
  const [maxPrice, setMaxPrice] = useState(searchParams.get('max_price') ?? '')
  const [ordering, setOrdering] = useState(searchParams.get('ordering') || '')
  const [page, setPage] = useState(parseInt(searchParams.get('page')) || 1)
  const pageSize = 12

  const loadCategory = useCallback(async () => {
    try {
      const data = await categoriesService.getCategoryBySlug(slug)
      if (data) {
        setCategory(data)
      } else {
        // Try to find in full list
        const allCategories = await categoriesService.getCategories()
        const catList = Array.isArray(allCategories)
          ? allCategories
          : allCategories.results || []
        const found = catList.find(cat => cat.slug === slug)
        setCategory(found || null)
      }
    } catch (error) {
      console.error('Error loading category:', error)
    }
  }, [slug])

  useEffect(() => {
    loadCategory()
  }, [loadCategory])

  const loadProducts = useCallback(async () => {
    setLoading(true)
    try {
      const params = {
        category: category?.id || slug,
        page,
        page_size: pageSize,
      }

      if (search) params.search = search
      if (minPrice !== '') params.min_price = minPrice
      if (maxPrice !== '') params.max_price = maxPrice
      if (ordering) params.ordering = ordering

      const data = await productsService.getProducts(params)
      setProducts(Array.isArray(data) ? data : data.results || [])
      setPagination({
        count: data.count || 0,
        next: data.next,
        previous: data.previous,
        totalPages: Math.ceil((data.count || 0) / pageSize),
      })

    } catch (error) {
      toastRef.current?.error?.('Error al cargar productos')
      console.error('Error loading products:', error)
    } finally {
      setLoading(false)
    }
  }, [category?.id, slug, page, pageSize, search, minPrice, maxPrice, ordering])

  useEffect(() => {
    if (category) {
      loadProducts()
    }
  }, [category, loadProducts])

  const urlFilters = useMemo(() => ({
    page: parseInt(searchParams.get('page')) || 1,
    search: searchParams.get('search') || '',
    minPrice: searchParams.get('min_price') ?? '',
    maxPrice: searchParams.get('max_price') ?? '',
    ordering: searchParams.get('ordering') || '',
  }), [searchParams])

  // Sincronizar estado cuando la URL cambie externamente (navegación, back/forward)
  const isFirstSync = useRef(true)

  useEffect(() => {
    if (urlFilters.page !== page) {
      setPage(urlFilters.page)
    }

    if (urlFilters.search !== search) {
      setSearch(urlFilters.search)
    }

    if (urlFilters.minPrice !== minPrice) {
      setMinPrice(urlFilters.minPrice)
    }

    if (urlFilters.maxPrice !== maxPrice) {
      setMaxPrice(urlFilters.maxPrice)
    }

    if (urlFilters.ordering !== ordering) {
      setOrdering(urlFilters.ordering)
    }

    querySyncRef.current = searchParams.toString()
  }, [urlFilters, page, search, minPrice, maxPrice, ordering, searchParams])

  useEffect(() => {
    toastRef.current = toast
  }, [toast])

  // Actualizar los parámetros de la URL cuando cambien los filtros / página
  useEffect(() => {
    if (isFirstSync.current) {
      isFirstSync.current = false
      querySyncRef.current = searchParams.toString()
      return
    }

    const params = new URLSearchParams()
    params.set('page', page.toString())
    params.set('page_size', pageSize.toString())
    if (search) {
      params.set('search', search)
    }
    if (minPrice !== '') {
      params.set('min_price', minPrice)
    }
    if (maxPrice !== '') {
      params.set('max_price', maxPrice)
    }
    if (ordering) {
      params.set('ordering', ordering)
    }

    const serialized = params.toString()
    if (querySyncRef.current !== serialized) {
      querySyncRef.current = serialized
      setSearchParams(params, { replace: true })
    }
  }, [page, pageSize, search, minPrice, maxPrice, ordering, setSearchParams, searchParams])

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
  }

  const handleFilterChange = () => {
    setPage(1)
  }

  const handleAddToCart = async (product, quantity = 1) => {
    if (product.stock_qty === 0) {
      toast.error('Producto sin stock')
      return
    }

    try {
      // ✅ Enviar cantidad exacta al backend (sin límites artificiales)
      await cartService.addToCart({
        product_id: product.id,
        quantity, // Usar la cantidad seleccionada directamente
      })

      // ✅ MEJORA: Recargar carrito completo desde backend
      // addToCart() solo devuelve { message, cart_id }, no items
      const { fetchCart } = useCartStore.getState()
      await fetchCart()
      
      // Mostrar toast de éxito
      toast.success('Producto agregado al carrito')
    } catch (error) {
      console.error('Error adding to cart:', error)
      toast.error(error.response?.data?.error || 'Error al agregar al carrito')
      
      // Recargar carrito para sincronizar con servidor en caso de error
      try {
        const { fetchCart } = useCartStore.getState()
        await fetchCart()
      } catch (err) {
        console.error('Error refreshing cart after error:', err)
      }
    }
  }

  const orderOptions = [
    { value: '', label: 'Sin orden' },
    { value: 'price', label: 'Precio: Menor a Mayor' },
    { value: '-price', label: 'Precio: Mayor a Menor' },
    { value: 'name', label: 'Nombre: A-Z' },
    { value: '-name', label: 'Nombre: Z-A' },
  ]

  if (loading && !category) {
    return (
      <div className="min-h-screen flex justify-center items-center">
        <Spinner size="lg" />
      </div>
    )
  }

  if (!category) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Categoría no encontrada</h2>
            <Link to="/">
              <Button>Volver al inicio</Button>
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Breadcrumb */}
        <nav className="mb-4 text-sm text-gray-600">
          <Link to="/" className="hover:text-primary-600 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:rounded">
            Inicio
          </Link>
          <span className="mx-2">/</span>
          <span className="text-gray-900 font-medium">{category.name}</span>
        </nav>

        {/* Category Title */}
        <h1 className="text-3xl font-bold text-gray-900 mb-8">{category.name}</h1>

        {/* Filters */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <form onSubmit={handleSearch} className="mb-6">
            <div className="flex gap-4">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar productos..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <Button type="submit">Buscar</Button>
            </div>
          </form>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Precio Mínimo
              </label>
              <input
                type="number"
                value={minPrice}
                onChange={(e) => {
                  setMinPrice(e.target.value)
                  handleFilterChange()
                }}
                placeholder="0"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Precio Máximo
              </label>
              <input
                type="number"
                value={maxPrice}
                onChange={(e) => {
                  setMaxPrice(e.target.value)
                  handleFilterChange()
                }}
                placeholder="999999"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ordenar por
              </label>
              <select
                value={ordering}
                onChange={(e) => {
                  setOrdering(e.target.value)
                  handleFilterChange()
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {orderOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Products Grid */}
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <Spinner size="lg" />
          </div>
        ) : products.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <p className="text-gray-500 text-lg">No hay productos disponibles</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
              {products.map((product) => (
                <ProductCardWithCart
                  key={product.id}
                  product={product}
                  onAddToCart={handleAddToCart}
                />
              ))}
            </div>

            {/* Pagination */}
            {pagination.totalPages > 1 && (
              <div className="flex justify-center items-center gap-4">
                <Button
                  variant="outline"
                  onClick={() => setPage(page - 1)}
                  disabled={!pagination.previous || page === 1}
                >
                  Anterior
                </Button>
                <span className="text-gray-700">
                  Página {page} de {pagination.totalPages}
                </span>
                <Button
                  variant="outline"
                  onClick={() => setPage(page + 1)}
                  disabled={!pagination.next || page === pagination.totalPages}
                >
                  Siguiente
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default CategoryPage

