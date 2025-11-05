import { useState, useEffect } from 'react'
import { Link, useNavigate, useSearchParams, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store/authSlice'
import { useCartStore } from '../../store/cartSlice'
import Button from './Button'
import condorBrand from '../../assets/condor-brand.svg'

const Header = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  
  // Acceso seguro a stores con defaults - usar selector seguro
  const isAuthenticated = useAuthStore((state) => state?.isAuthenticated ?? false)
  const role = useAuthStore((state) => state?.role ?? null)
  const logout = useAuthStore((state) => state?.logout ?? (() => {}))
  
  const itemCount = useCartStore((state) => {
    try {
      return typeof state?.getItemCount === 'function' ? state.getItemCount() : 0
    } catch {
      return 0
    }
  })
  
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '')

  // Update search query when URL changes
  useEffect(() => {
    const urlSearch = searchParams.get('search') || ''
    setSearchQuery(urlSearch)
  }, [searchParams])

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const handleSearch = (e) => {
    e.preventDefault()
    const query = searchQuery.trim()
    
    if (query) {
      // Navigate to home with search param
      if (location.pathname === '/') {
        // Update URL and trigger search in Home
        navigate(`/?search=${encodeURIComponent(query)}`, { replace: true })
        // Force reload products in Home by dispatching custom event
        window.dispatchEvent(new CustomEvent('searchProducts', { detail: query }))
      } else {
        navigate(`/?search=${encodeURIComponent(query)}`)
      }
    } else {
      // Clear search
      if (location.pathname === '/') {
        navigate('/', { replace: true })
        window.dispatchEvent(new CustomEvent('searchProducts', { detail: '' }))
      } else {
        navigate('/')
      }
    }
  }

  return (
    <header className="bg-white shadow-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto pl-2 pr-4 sm:pl-4 sm:pr-6 lg:px-8">
        {/* Desktop Layout */}
        <div className="hidden lg:flex justify-between items-center h-16">
          {/* Left: Brand */}
          <Link to="/" className="flex items-center" aria-label="CondorShop">
            <img 
              src={condorBrand} 
              alt="CondorShop brand logo featuring a black silhouette of a condor with open wings perched on a stylized mountain" 
              className="mr-2"
              style={{ height: '34px', width: 'auto' }}
            />
            <h1 className="text-2xl font-bold text-black">CondorShop</h1>
          </Link>

          {/* Center: Search Bar */}
          <form onSubmit={handleSearch} className="flex items-center">
            <div className="flex items-center" style={{ width: '520px', minWidth: '420px' }}>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Buscar productos…"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <Button
                type="submit"
                variant="primary"
                className="rounded-l-none rounded-r-lg"
              >
                Buscar
              </Button>
            </div>
          </form>

          {/* Right: Navigation Links + Cart */}
          <div className="flex items-center space-x-4">
            <nav className="flex items-center space-x-4">
              <Link
                to="/"
                className="text-black hover:text-primary-600 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:rounded"
              >
                Inicio
              </Link>
              
              {isAuthenticated ? (
                <>
                  <Link
                    to="/profile"
                    className="text-black hover:text-primary-600 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:rounded"
                  >
                    Mi Perfil
                  </Link>
                  <Link
                    to="/orders"
                    className="text-black hover:text-primary-600 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:rounded"
                  >
                    Mis Pedidos
                  </Link>
                  {role === 'admin' && (
                    <Link
                      to="/admin"
                      className="text-primary-600 font-semibold hover:text-primary-700 transition-colors flex items-center gap-1 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:rounded"
                    >
                      <span>Admin</span>
                      <span className="bg-primary-600 text-white text-xs px-2 py-0.5 rounded-full">
                        Admin
                      </span>
                    </Link>
                  )}
                  <Button variant="ghost" size="sm" onClick={handleLogout}>
                    Cerrar Sesión
                  </Button>
                </>
              ) : (
                <>
                  <Link to="/login">
                    <Button variant="ghost" size="sm">
                      Iniciar Sesión
                    </Button>
                  </Link>
                  <Link to="/register">
                    <Button size="sm">Registrarse</Button>
                  </Link>
                </>
              )}
            </nav>

            {/* Cart Button with Badge */}
            <Link
              to="/cart"
              className="relative inline-flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
              aria-label={`Carrito con ${itemCount} ${itemCount === 1 ? 'item' : 'items'}`}
            >
              <svg
                className="w-5 h-5 text-gray-700"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
              <span className="hidden md:inline-block text-sm font-medium text-gray-700">
                Carrito
              </span>
              {itemCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center border-2 border-white">
                  {itemCount > 99 ? '99+' : itemCount}
                </span>
              )}
            </Link>
          </div>
        </div>

        {/* Mobile/Tablet Layout */}
        <div className="lg:hidden">
          {/* Row 1: Brand + Cart */}
          <div className="flex justify-between items-center h-14">
            <Link to="/" className="flex items-center" aria-label="CondorShop">
              <img 
                src={condorBrand} 
                alt="CondorShop brand logo featuring a black silhouette of a condor with open wings perched on a stylized mountain" 
                className="mr-2"
                style={{ height: '34px', width: 'auto' }}
              />
              <h1 className="text-xl font-bold text-black">CondorShop</h1>
            </Link>

            {/* Cart Button - Mobile (icon only) */}
            <Link
              to="/cart"
              className="relative p-2 text-gray-700 hover:text-primary-600 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:rounded"
              aria-label={`Carrito con ${itemCount} ${itemCount === 1 ? 'item' : 'items'}`}
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
              {itemCount > 0 && (
                <span className="absolute top-0 right-0 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                  {itemCount > 99 ? '99+' : itemCount}
                </span>
              )}
            </Link>
          </div>

          {/* Row 2: Search Bar */}
          <form onSubmit={handleSearch} className="pb-3">
            <div className="flex items-center w-full">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Buscar productos…"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <Button
                type="submit"
                variant="primary"
                className="rounded-l-none rounded-r-lg"
              >
                Buscar
              </Button>
            </div>
          </form>

          {/* Row 3: Navigation Links */}
          <nav className="flex items-center space-x-2 pb-3">
            <Link
              to="/"
              className="text-sm text-black hover:text-primary-600 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:rounded"
            >
              Inicio
            </Link>
            {isAuthenticated ? (
              <>
                <span className="text-gray-300">|</span>
                <Link
                  to="/profile"
                  className="text-sm text-black hover:text-primary-600 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:rounded"
                >
                  Perfil
                </Link>
                <span className="text-gray-300">|</span>
                <Link
                  to="/orders"
                  className="text-sm text-black hover:text-primary-600 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:rounded"
                >
                  Pedidos
                </Link>
                {role === 'admin' && (
                  <>
                    <span className="text-gray-300">|</span>
                    <Link
                      to="/admin"
                      className="text-sm text-primary-600 font-semibold hover:text-primary-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:rounded"
                    >
                      Admin
                    </Link>
                  </>
                )}
                <span className="text-gray-300">|</span>
                <button
                  onClick={handleLogout}
                  className="text-sm text-black hover:text-primary-600 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:rounded"
                >
                  Salir
                </button>
              </>
            ) : (
              <>
                <span className="text-gray-300">|</span>
                <Link
                  to="/login"
                  className="text-sm text-black hover:text-primary-600 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:rounded"
                >
                  Iniciar Sesión
                </Link>
                <span className="text-gray-300">|</span>
                <Link
                  to="/register"
                  className="text-sm text-black hover:text-primary-600 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:rounded"
                >
                  Registrarse
                </Link>
              </>
            )}
          </nav>
        </div>
      </div>
    </header>
  )
}

export default Header
