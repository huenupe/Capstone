import { useState } from 'react'

/**
 * Componente de imagen optimizado para mejorar LCP y rendimiento
 * 
 * Características:
 * - Lazy loading para imágenes fuera del viewport
 * - fetchpriority para imágenes críticas (LCP)
 * - width/height para evitar layout shift
 * - decoding async para mejor rendimiento
 * - Placeholder mientras carga
 */
const OptimizedImage = ({
  src,
  alt,
  className = '',
  width,
  height,
  priority = false, // Para imágenes críticas (LCP)
  onError,
  ...props
}) => {
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)

  const handleLoad = () => {
    setIsLoading(false)
  }

  const handleError = (e) => {
    setIsLoading(false)
    setHasError(true)
    if (onError) {
      onError(e)
    } else {
      // Fallback por defecto
      e.target.src = '/placeholder-product.jpg'
    }
  }

  return (
    <div className="relative inline-block">
      {isLoading && !hasError && (
        <div 
          className="absolute inset-0 bg-gray-200 animate-pulse rounded"
          aria-hidden="true"
        />
      )}
      <img
        src={src}
        alt={alt}
        width={width}
        height={height}
        loading={priority ? 'eager' : 'lazy'}
        fetchPriority={priority ? 'high' : 'auto'}
        decoding="async"
        className={`${className} ${isLoading ? 'opacity-0' : 'opacity-100'} transition-opacity duration-300`}
        onLoad={handleLoad}
        onError={handleError}
        {...props}
      />
    </div>
  )
}

export default OptimizedImage

