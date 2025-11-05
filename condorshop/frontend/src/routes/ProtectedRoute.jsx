import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/authSlice'

const ProtectedRoute = ({ children }) => {
  try {
    // Acceder al store de forma segura
    const store = useAuthStore()
    const isAuthenticated = store?.isAuthenticated ?? false

    // Si no está autenticado, redirigir a login
    if (!isAuthenticated) {
      return <Navigate to="/login" replace />
    }

    // Asegurar que siempre retornamos algo válido
    return children || null
  } catch (error) {
    // Si hay error accediendo al store, redirigir a login
    console.error('ProtectedRoute error:', error)
    return <Navigate to="/login" replace />
  }
}

export default ProtectedRoute





