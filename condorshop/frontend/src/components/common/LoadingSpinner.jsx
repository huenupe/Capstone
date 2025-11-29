/**
 * LoadingSpinner - Componente de carga para lazy loading de rutas
 * 
 * Muestra un spinner centrado mientras se cargan componentes lazy.
 * Optimizado para mejorar la experiencia de usuario durante code splitting.
 */
const LoadingSpinner = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="inline-block w-12 h-12 mb-4">
          <div className="animate-spin rounded-full border-4 border-gray-200 border-t-primary-600"></div>
        </div>
        <p className="text-gray-600 text-sm">Cargando...</p>
      </div>
    </div>
  )
}

export default LoadingSpinner

