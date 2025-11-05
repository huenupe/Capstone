import { BrowserRouter } from 'react-router-dom'
import { useEffect } from 'react'
import Header from './components/common/Header'
import Footer from './components/common/Footer'
import ToastContainer from './components/common/Toast'
import ErrorBoundary from './components/common/ErrorBoundary'
import AppRoutes from './routes/AppRoutes'
import { useAuthStore } from './store/authSlice'

function App() {
  useEffect(() => {
    // Initialize auth state from localStorage - solo una vez al montar
    try {
      const initialize = useAuthStore.getState()?.initialize
      if (typeof initialize === 'function') {
        initialize()
      }
    } catch (error) {
      // Error silencioso - la app debe funcionar sin autenticación
      console.error('Error initializing auth:', error)
    }
  }, []) // Solo ejecutar una vez al montar

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div className="flex flex-col min-h-screen">
          <ErrorBoundary>
            <Header />
          </ErrorBoundary>
          <main className="flex-grow">
            <ErrorBoundary>
              <AppRoutes />
            </ErrorBoundary>
          </main>
          <ErrorBoundary>
            <Footer />
          </ErrorBoundary>
          <ErrorBoundary>
            <ToastContainer />
          </ErrorBoundary>
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App

