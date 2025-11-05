"""
Servicios para envío de emails de confirmación de pedidos
"""
from django.core.mail import send_mail
from django.conf import settings


def send_order_confirmation_email(order):
    """
    Prepara el envío de email de confirmación de pedido
    Se completará cuando se integre Webpay
    """
    subject = f'Confirmación de pedido #{order.id} - CondorShop'
    message = f"""
    Hola {order.customer_name},

    Tu pedido #{order.id} ha sido confirmado.

    Total: ${order.total_amount:,.0f} CLP
    Estado: {order.status.description}

    Gracias por tu compra!

    CondorShop
    """
    
    # Por ahora solo prepara el email, no lo envía
    # Se implementará cuando se integre Webpay
    # send_mail(
    #     subject=subject,
    #     message=message,
    #     from_email=settings.DEFAULT_FROM_EMAIL,
    #     recipient_list=[order.customer_email],
    #     fail_silently=False,
    # )
    
    return True

