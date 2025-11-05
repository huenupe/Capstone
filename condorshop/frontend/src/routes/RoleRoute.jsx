import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/authSlice'

const RoleRoute = ({ children, requiredRole = 'admin' }) => {
  try {
    // Acceder al store de forma segura
    const store = useAuthStore()
    const isAuthenticated = store?.isAuthenticated ?? false
    const role = store?.role ?? null

    if (!isAuthenticated) {
      return <Navigate to="/login" replace />
    }

    if (role !== requiredRole) {
      return <Navigate to="/" replace />
    }

    // Asegurar que siempre retornamos algo válido
    return children || null
  } catch (error) {
    // Si hay error accediendo al store, redirigir a login
    console.error('RoleRoute error:', error)
    return <Navigate to="/login" replace />
  }
}

export default RoleRoute





