import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import Spinner from '../common/Spinner'
import { categoriesService } from '../../services/categories'

const CategoryGrid = () => {
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)

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
      // Loguear el error para debugging - es importante saber qué está pasando
      console.error('Error loading categories:', error)
      // Si el error es 404, puede ser que no haya categorías aún o el endpoint no exista
      // Esto es información útil para el desarrollador
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
    }
  }

  const getCategoryImage = (slug) => {
    // Try to load image from assets, fallback to placeholder
    // Using public path for category images
    return `/categories/${slug}.jpg`
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

  return (
    <div className="mb-12">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Categorías</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {categories.map((category) => (
          <Link
            key={category.id}
            to={`/category/${category.slug}`}
            className="group flex flex-col items-center text-center hover:opacity-80 transition-opacity focus:outline-none focus:ring-2 focus:ring-primary-500 focus:rounded-lg"
          >
            <div className="relative w-full aspect-square rounded-lg overflow-hidden bg-gray-100 mb-2">
              <img
                src={getCategoryImage(category.slug)}
                alt={category.name}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                onError={handleImageError}
              />
              {/* Placeholder gradient */}
              <div 
                className="category-placeholder hidden absolute inset-0 items-center justify-center bg-gradient-to-br from-primary-300 to-primary-500 text-white font-semibold"
              >
                {category.name.charAt(0)}
              </div>
            </div>
            <span className="text-sm font-medium text-gray-700 group-hover:text-primary-600 transition-colors">
              {category.name}
            </span>
          </Link>
        ))}
      </div>
    </div>
  )
}

export default CategoryGrid

