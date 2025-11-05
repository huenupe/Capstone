import { Routes, Route } from 'react-router-dom'
import ProtectedRoute from './ProtectedRoute'
import RoleRoute from './RoleRoute'

// Public pages
import Home from '../pages/Home'
import CategoryPage from '../pages/CategoryPage'
import ProductDetail from '../pages/ProductDetail'
import Cart from '../pages/Cart'
import Login from '../pages/Auth/Login'
import Register from '../pages/Auth/Register'

// Checkout steps
import StepCustomer from '../pages/Checkout/StepCustomer'
import StepAddress from '../pages/Checkout/StepAddress'
import StepPayment from '../pages/Checkout/StepPayment'
import StepReview from '../pages/Checkout/StepReview'

// Auth pages
import ForgotPassword from '../pages/Auth/ForgotPassword'
import ResetPassword from '../pages/Auth/ResetPassword'

// Protected pages (client)
import Profile from '../pages/Profile'
import Orders from '../pages/Orders'

// Admin pages
import AdminDashboard from '../pages/Admin/Dashboard'
import AdminProducts from '../pages/Admin/Products'
import AdminOrders from '../pages/Admin/Orders'

const AppRoutes = () => {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<Home />} />
      <Route path="/category/:slug" element={<CategoryPage />} />
      <Route path="/product/:slug" element={<ProductDetail />} />
      <Route path="/cart" element={<Cart />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />

      {/* Checkout routes (can be accessed by guests) */}
      <Route path="/checkout/customer" element={<StepCustomer />} />
      <Route path="/checkout/address" element={<StepAddress />} />
      <Route path="/checkout/payment" element={<StepPayment />} />
      <Route path="/checkout/review" element={<StepReview />} />

      {/* Protected routes (client) */}
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
        }
      />
      <Route
        path="/orders"
        element={
          <ProtectedRoute>
            <Orders />
          </ProtectedRoute>
        }
      />

      {/* Admin routes */}
      <Route
        path="/admin"
        element={
          <RoleRoute>
            <AdminDashboard />
          </RoleRoute>
        }
      />
      <Route
        path="/admin/products"
        element={
          <RoleRoute>
            <AdminProducts />
          </RoleRoute>
        }
      />
      <Route
        path="/admin/orders"
        element={
          <RoleRoute>
            <AdminOrders />
          </RoleRoute>
        }
      />

      {/* Catch-all route - debe ser la última */}
      <Route
        path="*"
        element={
          <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
            <div className="text-center">
              <h1 className="text-2xl font-bold text-gray-900 mb-4">404 - Página no encontrada</h1>
              <p className="text-gray-600 mb-4">La página que buscas no existe.</p>
              <a href="/" className="text-primary-600 hover:text-primary-700 underline">
                Volver al inicio
              </a>
            </div>
          </div>
        }
      />
    </Routes>
  )
}

export default AppRoutes

