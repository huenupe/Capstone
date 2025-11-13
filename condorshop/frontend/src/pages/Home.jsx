import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import HeroCarousel from '../components/home/HeroCarousel'
import CategoryGrid from '../components/home/CategoryGrid'
import ProductRail from '../components/home/ProductRail'
import ProductCard from '../components/products/ProductCard'
import Button from '../components/common/Button'
import Spinner from '../components/common/Spinner'
import { productsService } from '../services/products'
import { useToast } from '../components/common/Toast'

const Home = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({})
  const [showSearchResults, setShowSearchResults] = useState(false)
  const toast = useToast()

  const searchQuery = searchParams.get('search') || ''

  const loadSearchProducts = useCallback(async (query) => {
    if (!query.trim()) {
      setShowSearchResults(false)
      setProducts([])
      return
    }

    setLoading(true)
    try {
      const data = await productsService.getProducts({
        search: query,
        page_size: 12,
      })
      const productsList = Array.isArray(data) ? data : data.results || []
      setProducts(productsList)
      setPagination({
        count: data.count || productsList.length,
        next: data.next,
        previous: data.previous,
        totalPages: Math.ceil((data.count || productsList.length) / 12),
      })
    } catch (error) {
      toast.error('Error al buscar productos')
      console.error('Error searching products:', error)
    } finally {
      setLoading(false)
    }
  }, [toast])

  // Listen for search events from Header
  useEffect(() => {
    const handleSearch = (event) => {
      const query = event.detail || ''
      if (query) {
        setShowSearchResults(true)
        loadSearchProducts(query)
      } else {
        setShowSearchResults(false)
        setProducts([])
      }
    }

    window.addEventListener('searchProducts', handleSearch)
    return () => window.removeEventListener('searchProducts', handleSearch)
  }, [loadSearchProducts])

  // Load products if search param exists in URL (on mount or when search param changes)
  useEffect(() => {
    if (searchQuery) {
      if (!showSearchResults) {
        setShowSearchResults(true)
      }
      loadSearchProducts(searchQuery)
    } else {
      if (showSearchResults) {
        setShowSearchResults(false)
      }
      if (products.length > 0) {
        setProducts([])
      }
    }
  }, [searchQuery, loadSearchProducts, showSearchResults, products.length])

  // Show search results if there's a search query
  if (showSearchResults || searchQuery) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">
            Resultados de búsqueda
            {searchQuery && (
              <span className="text-lg font-normal text-gray-600 ml-2">
                para &quot;{searchQuery}&quot;
              </span>
            )}
          </h1>

          {loading ? (
            <div className="flex justify-center items-center py-12">
              <Spinner size="lg" />
            </div>
          ) : products.length === 0 ? (
            <div className="bg-white rounded-lg shadow-md p-12 text-center">
              <p className="text-gray-500 text-lg mb-4">No se encontraron productos</p>
              <Button onClick={() => {
                setSearchParams({})
                setShowSearchResults(false)
                window.location.href = '/'
              }}>
                Volver al inicio
              </Button>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
                {products.map((product) => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>

              {/* Pagination */}
              {pagination.totalPages > 1 && (
                <div className="flex justify-center items-center gap-4">
                  <Button
                    variant="outline"
                    onClick={() => {
                      const page = parseInt(searchParams.get('page')) || 1
                      setSearchParams({ search: searchQuery, page: page - 1 })
                      loadSearchProducts(searchQuery)
                    }}
                    disabled={!pagination.previous}
                  >
                    Anterior
                  </Button>
                  <span className="text-gray-700">
                    Página {parseInt(searchParams.get('page')) || 1} de {pagination.totalPages}
                  </span>
                  <Button
                    variant="outline"
                    onClick={() => {
                      const page = parseInt(searchParams.get('page')) || 1
                      setSearchParams({ search: searchQuery, page: page + 1 })
                      loadSearchProducts(searchQuery)
                    }}
                    disabled={!pagination.next}
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

  // Default Home view with carousel, categories, and rails
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 1. Hero Carousel */}
        <HeroCarousel />

        {/* 2. Category Grid */}
        <CategoryGrid />

        {/* 3. Product Rails */}
        <ProductRail
          title="Ofertas"
          params={{
            max_price: 50000,
            page_size: 10,
          }}
        />

        <ProductRail
          title="Populares"
          params={{
            ordering: '-created_at',
            page_size: 10,
          }}
        />
      </div>
    </div>
  )
}

export default Home
