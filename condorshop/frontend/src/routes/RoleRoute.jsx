import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/authSlice'

const RoleRoute = ({ children, requiredRole = 'admin' }) => {
  const { isAuthenticated, role } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (role !== requiredRole) {
    return <Navigate to="/" replace />
  }

  return children
}

export default RoleRoute





