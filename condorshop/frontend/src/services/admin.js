import apiClient from './apiClient'

export const adminService = {
  // Productos
  /**
   * Obtener lista de productos (admin)
   */
  getProducts: async (params = {}) => {
    const response = await apiClient.get('/admin/products', { params })
    return response.data
  },

  /**
   * Crear producto
   * @param {FormData} formData - Datos del producto con imágenes
   */
  createProduct: async (formData) => {
    const response = await apiClient.post('/admin/products', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * Actualizar producto
   * @param {number} id - ID del producto
   * @param {FormData} formData - Datos actualizados
   */
  updateProduct: async (id, formData) => {
    const response = await apiClient.patch(`/admin/products/${id}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * Eliminar producto
   * @param {number} id - ID del producto
   */
  deleteProduct: async (id) => {
    const response = await apiClient.delete(`/admin/products/${id}`)
    return response.data
  },

  /**
   * Subir imágenes a un producto
   * @param {number} id - ID del producto
   * @param {FormData} formData - Archivos de imágenes
   */
  uploadProductImages: async (id, formData) => {
    const response = await apiClient.post(`/admin/products/${id}/images`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // Pedidos
  /**
   * Obtener lista de pedidos (admin)
   */
  getOrders: async (params = {}) => {
    const response = await apiClient.get('/admin/orders', { params })
    return response.data
  },

  /**
   * Cambiar estado de un pedido
   * @param {number} id - ID del pedido
   * @param {Object} data - { status_id }
   */
  updateOrderStatus: async (id, data) => {
    const response = await apiClient.patch(`/admin/orders/${id}/status`, data)
    return response.data
  },

  /**
   * Exportar pedidos a CSV
   * @param {Object} params - Filtros opcionales
   */
  exportOrders: async (params = {}) => {
    const response = await apiClient.get('/admin/orders/export', {
      params,
      responseType: 'blob',
    })
    return response.data
  },

  /**
   * Obtener estados de pedidos
   */
  getOrderStatuses: async () => {
    const response = await apiClient.get('/admin/order-statuses')
    return response.data
  },
}





