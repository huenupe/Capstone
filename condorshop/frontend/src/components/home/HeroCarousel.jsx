import { useState, useEffect } from 'react'
import { commonService } from '../../services/common'
import Spinner from '../common/Spinner'

const HeroCarousel = () => {
  const [currentSlide, setCurrentSlide] = useState(0)
  const [slides, setSlides] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Cargar slides del backend
  useEffect(() => {
    let isMounted = true // Flag para evitar actualizar estado si el componente se desmonta

    const loadSlides = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await commonService.getHeroCarouselSlides()
        
        // Verificar que el componente aún esté montado
        if (!isMounted) return
        
        // Validar y ordenar slides
        if (!Array.isArray(data)) {
          console.warn('[HeroCarousel] Datos recibidos no son un array:', data)
          if (isMounted) {
            setSlides([])
            setError('Formato de datos inválido')
          }
          return
        }
        
        // Filtrar slides válidos y ordenar por 'order'
        const validSlides = data
          .filter(slide => slide && slide.id && slide.image_url)
          .sort((a, b) => (a.order || 0) - (b.order || 0))
        
        if (isMounted) {
          setSlides(validSlides)
          if (validSlides.length === 0 && data.length > 0) {
            setError('Las imágenes no están disponibles')
          }
        }
      } catch (err) {
        console.error('[HeroCarousel] Error al cargar slides:', err)
        if (isMounted) {
          setError('No se pudieron cargar las imágenes del carrusel')
          setSlides([]) // Fallback a array vacío
        }
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    loadSlides()
    
    // Cleanup: prevenir actualizaciones de estado si el componente se desmonta
    return () => {
      isMounted = false
    }
  }, [])

  // Auto-play cuando hay slides
  useEffect(() => {
    if (slides.length === 0) return

    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slides.length)
    }, 5000) // Auto-play every 5 seconds

    return () => clearInterval(timer)
  }, [slides.length])

  const goToSlide = (index) => {
    setCurrentSlide(index)
  }

  const goToPrevious = () => {
    setCurrentSlide((prev) => (prev - 1 + slides.length) % slides.length)
  }

  const goToNext = () => {
    setCurrentSlide((prev) => (prev + 1) % slides.length)
  }

  const handleImageError = (e) => {
    // Fallback to gradient placeholder if image doesn't exist
    console.warn('[HeroCarousel] Error al cargar imagen:', e.target.src)
    e.target.style.display = 'none'
    const placeholder = e.target.parentElement?.parentElement?.querySelector('.placeholder-gradient')
    if (placeholder) {
      placeholder.style.display = 'flex'
    }
  }

  // Mostrar spinner mientras carga
  if (loading) {
    return (
      <div className="relative w-full h-[400px] md:h-[500px] lg:h-[600px] overflow-hidden bg-gray-200 flex items-center justify-center">
        <Spinner />
      </div>
    )
  }

  // Mostrar mensaje de error o placeholder si no hay slides
  if (error || slides.length === 0) {
    return (
      <div className="relative w-full h-[400px] md:h-[500px] lg:h-[600px] overflow-hidden bg-gradient-to-r from-primary-400 to-primary-600 flex items-center justify-center text-white text-xl">
        {error || 'No hay imágenes disponibles en el carrusel'}
      </div>
    )
  }

  return (
    <div className="relative w-full h-[400px] md:h-[500px] lg:h-[600px] overflow-hidden bg-gray-900">
      {/* Slides */}
      {slides.map((slide, index) => (
        <div
          key={slide.id}
          className={`absolute inset-0 transition-opacity duration-700 ${
            index === currentSlide ? 'opacity-100 z-10' : 'opacity-0 z-0'
          }`}
        >
          <img
            src={slide.image_url}
            alt={slide.alt_text || slide.name || 'Slide del carrusel'}
            className="w-full h-full object-cover object-center"
            onError={handleImageError}
            loading={index === 0 ? 'eager' : 'lazy'}
          />
          {/* Placeholder gradient if image fails to load */}
          <div 
            className="placeholder-gradient hidden absolute inset-0 w-full h-full items-center justify-center bg-gradient-to-r from-primary-400 to-primary-600 text-white text-2xl font-bold px-4 text-center"
          >
            {slide.alt_text || slide.name || 'Slide del carrusel'}
          </div>
        </div>
      ))}

      {/* Navigation Arrows */}
      <button
        onClick={goToPrevious}
        className="absolute left-4 top-1/2 transform -translate-y-1/2 z-20 bg-white/80 hover:bg-white rounded-full p-2 shadow-lg transition-all focus:outline-none focus:ring-2 focus:ring-primary-500"
        aria-label="Slide anterior"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      <button
        onClick={goToNext}
        className="absolute right-4 top-1/2 transform -translate-y-1/2 z-20 bg-white/80 hover:bg-white rounded-full p-2 shadow-lg transition-all focus:outline-none focus:ring-2 focus:ring-primary-500"
        aria-label="Slide siguiente"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>

      {/* Dots Indicator */}
      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-20 flex gap-2">
        {slides.map((_, index) => (
          <button
            key={index}
            onClick={() => goToSlide(index)}
            className={`w-3 h-3 rounded-full transition-all focus:outline-none focus:ring-2 focus:ring-primary-500 ${
              index === currentSlide
                ? 'bg-white w-8'
                : 'bg-white/50 hover:bg-white/75'
            }`}
            aria-label={`Ir al slide ${index + 1}`}
          />
        ))}
      </div>
    </div>
  )
}

export default HeroCarousel





