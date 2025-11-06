import apiClient from './apiClient'

export const usersService = {
  /**
   * Obtener direcciones guardadas del usuario
   * GET /api/users/addresses
   */
  getAddresses: async () => {
    const response = await apiClient.get('/users/addresses')
    return response.data
  },

  /**
   * Crear nueva dirección
   * POST /api/users/addresses
   * @param {Object} addressData - Datos de la dirección
   */
  createAddress: async (addressData) => {
    const response = await apiClient.post('/users/addresses', addressData)
    return response.data
  },

  /**
   * Actualizar dirección existente
   * PATCH /api/users/addresses/{id}
   * @param {number} addressId - ID de la dirección
   * @param {Object} addressData - Datos actualizados
   */
  updateAddress: async (addressId, addressData) => {
    const response = await apiClient.patch(`/users/addresses/${addressId}`, addressData)
    return response.data
  },

  /**
   * Eliminar dirección
   * DELETE /api/users/addresses/{id}
   * @param {number} addressId - ID de la dirección
   */
  deleteAddress: async (addressId) => {
    await apiClient.delete(`/users/addresses/${addressId}`)
  },

  /**
   * Obtener información del modo de checkout (incluye direcciones guardadas)
   * GET /api/checkout/mode
   */
  getCheckoutMode: async () => {
    const response = await apiClient.get('/checkout/mode')
    return response.data
  },
}

