import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import paymentsService from '../services/paymentsService';
import { formatPrice } from '../utils/formatPrice';

/**
 * Página de resultado de pago de Webpay
 * URL: /payment/result?status=success&order_id=123
 */
const PaymentResultPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [orderData, setOrderData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    verifyPayment();
  }, []);

  const verifyPayment = async () => {
    try {
      const status = searchParams.get('status');
      const orderId = searchParams.get('order_id') || sessionStorage.getItem('pending_order_id');
      const errorMessage = searchParams.get('message');

      console.log('Verificando pago:', { status, orderId, errorMessage });

      if (!orderId) {
        setError('No se encontró información de la orden');
        setLoading(false);
        return;
      }

      // Consultar estado de la orden
      const paymentData = await paymentsService.getPaymentStatus(orderId);
      console.log('Estado de pago:', paymentData);

      setOrderData(paymentData);
      setPaymentStatus(status);
      setLoading(false);

      // Limpiar sessionStorage
      sessionStorage.removeItem('pending_order_id');
      sessionStorage.removeItem('pending_order_amount');

    } catch (err) {
      console.error('Error al verificar pago:', err);
      setError('Error al verificar el estado del pago');
      setLoading(false);
    }
  };

  const handleGoToOrders = () => {
    navigate('/orders');
  };

  const handleGoToHome = () => {
    navigate('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
          <p className="text-lg text-gray-700">Verificando tu pago...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-100 mb-4">
              <svg className="h-8 w-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Error</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <button
              onClick={handleGoToHome}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Volver al inicio
            </button>
          </div>
        </div>
      </div>
    );
  }

  // PAGO EXITOSO
  if (paymentStatus === 'success' && orderData?.order_status === 'PAID') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-blue-50 p-4">
        <div className="max-w-2xl w-full bg-white rounded-lg shadow-xl p-8">
          <div className="text-center">
            {/* Ícono de éxito */}
            <div className="mx-auto flex items-center justify-center h-20 w-20 rounded-full bg-green-100 mb-6 animate-bounce">
              <svg className="h-12 w-12 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 mb-2">¡Pago Exitoso!</h1>
            <p className="text-lg text-gray-600 mb-8">
              Tu compra ha sido procesada correctamente
            </p>

            {/* Información del pago - Requerimientos de Transbank */}
            <div className="bg-gray-50 rounded-lg p-6 mb-8 text-left">
              <div className="grid grid-cols-2 gap-4">
                {/* Número de orden de pedido */}
                <div>
                  <p className="text-sm text-gray-500 mb-1">Número de Orden</p>
                  <p className="text-lg font-semibold text-gray-900">#{orderData.order_id}</p>
                </div>
                
                {/* Nombre del comercio */}
                <div>
                  <p className="text-sm text-gray-500 mb-1">Comercio</p>
                  <p className="text-lg font-semibold text-gray-900">CondorShop</p>
                </div>
                
                {/* Monto y moneda */}
                <div>
                  <p className="text-sm text-gray-500 mb-1">Monto Pagado</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {formatPrice(orderData.amount || 0)} {orderData.currency || 'CLP'}
                  </p>
                </div>
                
                {/* Fecha de transacción */}
                {orderData.transaction_data?.transaction_date && (
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Fecha de Transacción</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {new Date(orderData.transaction_data.transaction_date).toLocaleString('es-CL', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </p>
                  </div>
                )}
                
                {/* Código de autorización */}
                {orderData.transaction_data?.authorization_code && (
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Código de Autorización</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {orderData.transaction_data.authorization_code}
                    </p>
                  </div>
                )}
                
                {/* Tipo de pago (Débito o Crédito) */}
                {orderData.transaction_data?.card_brand && (
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Tipo de Pago</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {orderData.transaction_data.card_brand}
                    </p>
                  </div>
                )}
                
                {/* Cantidad de cuotas */}
                {orderData.transaction_data?.installments_number && (
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Cantidad de Cuotas</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {orderData.transaction_data.installments_number} {orderData.transaction_data.installments_number === 1 ? 'cuota' : 'cuotas'}
                    </p>
                  </div>
                )}
                
                {/* Cuatro últimos dígitos de la tarjeta */}
                {orderData.transaction_data?.card_last_four && (
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Tarjeta</p>
                    <p className="text-lg font-semibold text-gray-900">
                      **** {orderData.transaction_data.card_last_four}
                    </p>
                  </div>
                )}
              </div>
              
              {/* Descripción de los bienes y/o servicios */}
              {orderData.items && orderData.items.length > 0 && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <p className="text-sm font-semibold text-gray-700 mb-3">Productos adquiridos:</p>
                  <div className="space-y-2">
                    {orderData.items.map((item, index) => (
                      <div key={index} className="flex justify-between text-sm">
                        <span className="text-gray-600">
                          {item.quantity}x {item.name}
                        </span>
                        <span className="text-gray-900 font-medium">
                          {formatPrice(item.total_price || 0)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Mensaje de confirmación */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-8">
              <p className="text-sm text-blue-800">
                📧 Hemos enviado un correo de confirmación con los detalles de tu compra
              </p>
            </div>

            {/* Botones de acción */}
            <div className="flex flex-col sm:flex-row gap-4">
              <button
                onClick={handleGoToOrders}
                className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors font-semibold"
              >
                Ver mis pedidos
              </button>
              <button
                onClick={handleGoToHome}
                className="flex-1 bg-gray-200 text-gray-800 py-3 px-6 rounded-lg hover:bg-gray-300 transition-colors font-semibold"
              >
                Volver al inicio
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // PAGO FALLIDO
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-50 p-4">
      <div className="max-w-2xl w-full bg-white rounded-lg shadow-xl p-8">
        <div className="text-center">
          {/* Ícono de error */}
          <div className="mx-auto flex items-center justify-center h-20 w-20 rounded-full bg-red-100 mb-6">
            <svg className="h-12 w-12 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>

          <h1 className="text-3xl font-bold text-gray-900 mb-2">Pago No Completado</h1>
          <p className="text-lg text-gray-600 mb-8">
            Tu pago no pudo ser procesado
          </p>

          {/* Información del intento */}
          <div className="bg-gray-50 rounded-lg p-6 mb-8 text-left">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500 mb-1">Número de Orden</p>
                <p className="text-lg font-semibold text-gray-900">#{orderData?.order_id}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-1">Estado</p>
                <p className="text-lg font-semibold text-red-600">
                  {orderData?.order_status_name || 'Pago Fallido'}
                </p>
              </div>
            </div>
          </div>

          {/* Mensaje de ayuda */}
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-8">
            <p className="text-sm text-orange-800">
              ℹ️ El pago fue rechazado por la institución financiera. 
              Por favor, verifica los datos de tu tarjeta o intenta con otro método de pago.
            </p>
          </div>

          {/* Botones de acción */}
          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={() => navigate('/checkout/review')}
              className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors font-semibold"
            >
              Intentar nuevamente
            </button>
            <button
              onClick={handleGoToHome}
              className="flex-1 bg-gray-200 text-gray-800 py-3 px-6 rounded-lg hover:bg-gray-300 transition-colors font-semibold"
            >
              Volver al inicio
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentResultPage;

