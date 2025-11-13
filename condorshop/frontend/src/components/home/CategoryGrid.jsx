import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import Spinner from '../common/Spinner'
import { categoriesService } from '../../services/categories'

const CategoryGrid = () => {
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [isScrollable, setIsScrollable] = useState(false)
  const sliderRef = useRef(null)

  useEffect(() => {
    loadCategories()
  }, [])

  const loadCategories = async () => {
    setLoading(true)
    try {
      const data = await categoriesService.getCategories()
      const categoriesList = Array.isArray(data) ? data : data.results || []
      setCategories(categoriesList)
    } catch (error) {
      // Mantener todos los errores visibles para debugging del proyecto
      console.error('Error loading categories:', error)
      if (error.response?.status === 404) {
        console.warn('Categories endpoint returned 404. This may mean:', {
          reason: 'No categories in database or endpoint not configured',
          endpoint: error.config?.url,
          suggestion: 'Check backend categories endpoint or create categories in admin panel'
        })
      }
      setCategories([]) // Asegurar que categories esté vacío en caso de error
    } finally {
      setLoading(false)
      requestAnimationFrame(() => {
        const slider = sliderRef.current
        if (slider) {
          setIsScrollable(slider.scrollWidth > slider.clientWidth + 4)
        }
      })
    }
  }

  const handleImageError = (e) => {
    // Fallback to gradient placeholder
    e.target.style.display = 'none'
    const placeholder = e.target.parentElement.querySelector('.category-placeholder')
    if (placeholder) {
      placeholder.style.display = 'flex'
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <Spinner size="lg" />
      </div>
    )
  }

  if (categories.length === 0) {
    // No mostrar nada si no hay categorías (no es error)
    return null
  }

  const scrollSlider = (direction) => {
    const slider = sliderRef.current
    if (!slider) return
    const offset = direction === 'left' ? -220 : 220
    slider.scrollBy({ left: offset, behavior: 'smooth' })
  }

  return (
    <div className="mb-12">
      <div className="flex items-center justify-between mb-4 border-b border-gray-200 pb-2">
        <h2 className="text-2xl font-bold text-gray-900">Busca por categorías</h2>
        {isScrollable && (
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => scrollSlider('left')}
              className="h-9 w-9 rounded-full border border-gray-300 bg-white text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
              aria-label="Desplazar categorías hacia la izquierda"
            >
              ‹
            </button>
            <button
              type="button"
              onClick={() => scrollSlider('right')}
              className="h-9 w-9 rounded-full border border-gray-300 bg-white text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
              aria-label="Desplazar categorías hacia la derecha"
            >
              ›
            </button>
          </div>
        )}
      </div>

      <div className="relative">
        <div
          ref={sliderRef}
          className="flex gap-4 overflow-x-auto scrollbar-hide pb-1"
        >
          {categories.map((category) => (
            <Link
              key={category.id}
              to={`/category/${category.slug}`}
              className="group flex min-w-[120px] max-w-[120px] flex-col items-center text-center hover:opacity-90 transition-opacity focus:outline-none focus:ring-2 focus:ring-primary-500 focus:rounded-lg"
            >
              <div className="relative flex h-28 w-28 items-center justify-center overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm group-hover:shadow-md transition-shadow">
                <img
                  src={category.image || `/categories/${category.slug}.jpg`}
                  alt={category.name}
                  className="h-full w-full object-cover"
                  onError={handleImageError}
                />
                <div
                  className="category-placeholder hidden absolute inset-0 items-center justify-center bg-gradient-to-br from-primary-300 to-primary-500 text-lg font-semibold text-white"
                >
                  {category.name.charAt(0)}
                </div>
              </div>
              <span className="mt-3 text-sm font-medium text-gray-700 group-hover:text-primary-600 transition-colors line-clamp-2">
                {category.name}
              </span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}

export default CategoryGrid

