import { BrowserRouter } from 'react-router-dom'
import { useEffect } from 'react'
import Header from './components/common/Header'
import Footer from './components/common/Footer'
import ToastContainer from './components/common/Toast'
import AppRoutes from './routes/AppRoutes'
import { useAuthStore } from './store/authSlice'

function App() {
  const { initialize } = useAuthStore()

  useEffect(() => {
    // Initialize auth state from localStorage
    initialize()
  }, [initialize])

  return (
    <BrowserRouter>
      <div className="flex flex-col min-h-screen">
        <Header />
        <main className="flex-grow">
          <AppRoutes />
        </main>
        <Footer />
        <ToastContainer />
      </div>
    </BrowserRouter>
  )
}

export default App

