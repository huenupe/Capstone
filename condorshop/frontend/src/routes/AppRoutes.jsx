import { Routes, Route } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import ProtectedRoute from './ProtectedRoute'
import LoadingSpinner from '../components/common/LoadingSpinner'

/**
 * Lazy loading de todas las páginas para code splitting.
 * 
 * Beneficios:
 * - Reduce el tamaño inicial del bundle (mejora LCP)
 * - Carga componentes solo cuando se necesitan
 * - Mejor caché: vendors y páginas por separado
 * - Carga paralela de chunks
 */

// Public pages - Lazy loaded
const Home = lazy(() => import('../pages/Home'))
const CategoryPage = lazy(() => import('../pages/CategoryPage'))
const ProductDetail = lazy(() => import('../pages/ProductDetail'))
const Cart = lazy(() => import('../pages/Cart'))
const Login = lazy(() => import('../pages/Auth/Login'))
const Register = lazy(() => import('../pages/Auth/Register'))

// Checkout steps - Lazy loaded
const StepCustomer = lazy(() => import('../pages/Checkout/StepCustomer'))
const StepAddress = lazy(() => import('../pages/Checkout/StepAddress'))
const StepPayment = lazy(() => import('../pages/Checkout/StepPayment'))
const StepReview = lazy(() => import('../pages/Checkout/StepReview'))
const PaymentResultPage = lazy(() => import('../pages/PaymentResultPage'))

// Auth pages - Lazy loaded
const ForgotPassword = lazy(() => import('../pages/Auth/ForgotPassword'))
const ResetPassword = lazy(() => import('../pages/Auth/ResetPassword'))

// Protected pages (client) - Lazy loaded
const Profile = lazy(() => import('../pages/Profile'))
const Orders = lazy(() => import('../pages/Orders'))

const AppRoutes = () => {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        {/* Public routes - Wrapped in Suspense for lazy loading */}
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
        
        {/* Payment result page (public, accessed after Webpay redirect) */}
        <Route path="/payment/result" element={<PaymentResultPage />} />

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
    </Suspense>
  )
}

export default AppRoutes

