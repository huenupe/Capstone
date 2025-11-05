import { useState, useEffect } from 'react'

const HeroCarousel = () => {
  const [currentSlide, setCurrentSlide] = useState(0)
  
  // Placeholder slides - can be replaced with real images
  const slides = [
    { 
      id: 1, 
      image: '/hero/slide1.jpg',
      alt: 'Ofertas especiales en productos seleccionados'
    },
    { 
      id: 2, 
      image: '/hero/slide2.jpg',
      alt: 'Nuevos productos disponibles'
    },
    { 
      id: 3, 
      image: '/hero/slide3.jpg',
      alt: 'Descuentos increíbles esta temporada'
    },
    { 
      id: 4, 
      image: '/hero/slide4.jpg',
      alt: 'Envío gratis en compras sobre $50.000'
    },
    { 
      id: 5, 
      image: '/hero/slide5.jpg',
      alt: 'Tendencias de la temporada'
    },
  ]

  useEffect(() => {
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
    e.target.style.display = 'none'
    const placeholder = e.target.parentElement.querySelector('.placeholder-gradient')
    if (placeholder) {
      placeholder.style.display = 'flex'
    }
  }

  return (
    <div className="relative w-full h-[360px] md:h-[480px] overflow-hidden bg-gray-200 rounded-lg mb-8">
      {/* Slides */}
      {slides.map((slide, index) => (
        <div
          key={slide.id}
          className={`absolute inset-0 transition-opacity duration-700 ${
            index === currentSlide ? 'opacity-100 z-10' : 'opacity-0 z-0'
          }`}
        >
          <img
            src={slide.image}
            alt={slide.alt}
            className="w-full h-full object-cover"
            onError={handleImageError}
          />
          {/* Placeholder gradient if image fails to load */}
          <div 
            className="placeholder-gradient hidden w-full h-full items-center justify-center bg-gradient-to-r from-primary-400 to-primary-600 text-white text-2xl font-bold"
          >
            {slide.alt}
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





