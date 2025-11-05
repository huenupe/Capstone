import React from 'react'

let errorLogged = false

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    // Solo loguear el primer error para no inundar logs
    if (!errorLogged) {
      console.error('Error capturado por ErrorBoundary:', error, errorInfo)
      errorLogged = true
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
            <h1 className="text-2xl font-bold text-red-600 mb-4">Error en la aplicación</h1>
            <p className="text-gray-700 mb-4">
              Ocurrió un error inesperado. Por favor, recarga la página.
            </p>
            <button
              onClick={() => {
                errorLogged = false
                window.location.reload()
              }}
              className="w-full bg-gray-800 text-white py-2 px-4 rounded-lg hover:bg-gray-900"
            >
              Recargar Página
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary

