/**
 * Servicio para manejar pagos con Webpay
 */
import apiClient from './apiClient';

const paymentsService = {
  /**
   * Inicia el proceso de pago con Webpay
   * @param {number} orderId - ID de la orden a pagar
   * @returns {Promise} - { token, url, order_id, amount }
   */
  async initiateWebpayPayment(orderId) {
    try {
      const response = await apiClient.post(`/checkout/${orderId}/pay/`);
      return response.data;
    } catch (error) {
      console.error('Error al iniciar pago Webpay:', error);
      throw error;
    }
  },

  /**
   * Consulta el estado de pago de una orden
   * @param {number} orderId - ID de la orden
   * @returns {Promise} - Estado de la orden y pago
   */
  async getPaymentStatus(orderId) {
    try {
      const response = await apiClient.get(`/payments/status/${orderId}/`);
      return response.data;
    } catch (error) {
      console.error('Error al consultar estado de pago:', error);
      throw error;
    }
  },

  /**
   * Redirige a Webpay con el token de pago
   * @param {string} token - Token de Webpay
   * @param {string} url - URL de Webpay
   */
  redirectToWebpay(token, url) {
    // Crear formulario dinámico para POST a Webpay
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = url;

    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'token_ws';
    input.value = token;

    form.appendChild(input);
    document.body.appendChild(form);
    
    console.log('Redirigiendo a Webpay...', { token: token.substring(0, 20) + '...', url });
    form.submit();
  }
};

export default paymentsService;

