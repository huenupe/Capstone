import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { formatPrice } from '../../utils/formatPrice'
import Spinner from '../../components/common/Spinner'
import { adminService } from '../../services/admin'
import { useToast } from '../../components/common/Toast'

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalOrders: 0,
    totalProducts: 0,
    totalRevenue: 0,
    pendingOrders: 0,
  })
  const [loading, setLoading] = useState(true)
  const toast = useToast()

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    setLoading(true)
    try {
      // Load orders
      const ordersData = await adminService.getOrders({ page_size: 1000 })
      const orders = Array.isArray(ordersData) ? ordersData : ordersData.results || []
      
      // Load products
      const productsData = await adminService.getProducts({ page_size: 1000 })
      const products = Array.isArray(productsData) ? productsData : productsData.results || []

      const totalOrders = orders.length
      const totalProducts = products.length
      const totalRevenue = orders.reduce((sum, order) => sum + (order.total_amount || 0), 0)
      const pendingOrders = orders.filter(
        (order) => order.status?.code === 'PENDING'
      ).length

      setStats({
        totalOrders,
        totalProducts,
        totalRevenue,
        pendingOrders,
      })
    } catch (error) {
      toast.error('Error al cargar estadísticas')
      console.error('Error loading stats:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex justify-center items-center">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Panel de Administración</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Total de Pedidos</h3>
            <p className="text-3xl font-bold text-gray-900">{stats.totalOrders}</p>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Pedidos Pendientes</h3>
            <p className="text-3xl font-bold text-yellow-600">{stats.pendingOrders}</p>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Total de Productos</h3>
            <p className="text-3xl font-bold text-gray-900">{stats.totalProducts}</p>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Ingresos Totales</h3>
            <p className="text-3xl font-bold text-green-600">{formatPrice(stats.totalRevenue)}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Link
            to="/admin/products"
            className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
          >
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Gestionar Productos</h2>
            <p className="text-gray-600">Crear, editar y eliminar productos del catálogo</p>
          </Link>

          <Link
            to="/admin/orders"
            className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
          >
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Gestionar Pedidos</h2>
            <p className="text-gray-600">Ver, filtrar y cambiar estados de pedidos</p>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Dashboard





