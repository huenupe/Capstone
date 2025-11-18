#!/usr/bin/env python
"""
Script de verificación completa de Webpay.
Ejecutar: python verify_webpay_complete.py
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'condorshop_api.settings')
django.setup()

from django.conf import settings
from apps.orders.services import webpay_service, _check_transbank, _get_transbank_imports
from apps.orders.models import Order, OrderStatus

def print_section(title):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def test_imports():
    print_section("1. VERIFICACIÓN DE IMPORTACIONES")
    
    try:
        available, error = _check_transbank()
        if available:
            print("✅ transbank-sdk está disponible")
        else:
            print(f"❌ transbank-sdk NO disponible: {error}")
            return False
        
        TransbankError, Transaction = _get_transbank_imports()
        print(f"✅ TransbankError importado: {TransbankError}")
        print(f"✅ Transaction importado: {Transaction}")
        
        # Verificar métodos
        if hasattr(Transaction, 'create'):
            print("✅ Transaction.create() existe")
        else:
            print("❌ Transaction.create() NO existe")
            return False
        
        if hasattr(Transaction, 'commit'):
            print("✅ Transaction.commit() existe")
        else:
            print("❌ Transaction.commit() NO existe")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error al importar: {e}")
        return False

def test_configuration():
    print_section("2. VERIFICACIÓN DE CONFIGURACIÓN")
    
    config = settings.WEBPAY_CONFIG
    print(f"Ambiente: {config['ENVIRONMENT']}")
    print(f"Commerce Code: {config['COMMERCE_CODE']}")
    print(f"API Key: {config['API_KEY'][:20]}...{config['API_KEY'][-10:]}")
    print(f"Return URL: {config['RETURN_URL']}")
    print(f"Final URL: {config['FINAL_URL']}")
    
    # Verificar credenciales de integración
    if config['ENVIRONMENT'] == 'integration':
        expected_commerce_code = '597055555532'
        expected_api_key = '579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C'
        
        if config['COMMERCE_CODE'] == expected_commerce_code:
            print("✅ Commerce Code correcto para integración")
        else:
            print(f"⚠️ Commerce Code incorrecto")
            print(f"   Esperado: {expected_commerce_code}")
            print(f"   Actual: {config['COMMERCE_CODE']}")
        
        if config['API_KEY'] == expected_api_key:
            print("✅ API Key correcto para integración")
        else:
            print(f"⚠️ API Key incorrecto - verifica tu .env")
    
    return True

def test_webpay_service():
    print_section("3. VERIFICACIÓN DE WEBPAY SERVICE")
    
    if webpay_service is None:
        print("❌ webpay_service es None")
        print("   El servicio no se inicializó correctamente")
        print("   Revisa los logs del servidor Django al iniciar")
        return False
    
    print("✅ webpay_service está disponible")
    print(f"✅ Ambiente configurado: {webpay_service.environment}")
    print(f"✅ Config: {webpay_service.config}")
    
    # Verificar que NO tenga self.Transaction
    if hasattr(webpay_service, 'Transaction'):
        print("⚠️ WARNING: webpay_service.Transaction existe")
        print("   Esto puede causar el error de 'missing self'")
        print("   DEBES ELIMINAR self.Transaction del __init__")
        return False
    else:
        print("✅ webpay_service NO tiene atributo Transaction (correcto)")
    
    return True

def test_create_transaction():
    print_section("4. PRUEBA DE CREAR TRANSACCIÓN")
    
    if webpay_service is None:
        print("❌ No se puede probar: webpay_service es None")
        return False
    
    # Buscar una orden pendiente
    try:
        pending_status = OrderStatus.objects.get(code='PENDING')
        order = Order.objects.filter(status=pending_status).first()
    except OrderStatus.DoesNotExist:
        print("⚠️ Estado PENDING no encontrado en la base de datos")
        return None
    
    if not order:
        print("⚠️ No hay órdenes pendientes para probar")
        print("   Crea una orden desde el frontend primero")
        return None
    
    print(f"✅ Orden encontrada: {order.id}")
    print(f"   Estado: {order.status.code}")
    print(f"   Monto: ${order.total_amount}")
    
    print("\n🔄 Intentando crear transacción...")
    try:
        success, token, data = webpay_service.create_transaction(order)
        
        if success:
            print("✅ ¡TRANSACCIÓN CREADA EXITOSAMENTE!")
            print(f"   Token: {token[:20]}...")
            print(f"   URL: {data.get('url', 'N/A')}")
            print(f"   Monto: ${data.get('amount', 'N/A')}")
            return True
        else:
            print(f"❌ Error al crear transacción: {token}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción al crear transacción: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print_section("VERIFICACIÓN COMPLETA DE WEBPAY")
    print("Este script verifica toda la configuración de Webpay")
    
    results = {
        'imports': test_imports(),
        'config': test_configuration(),
        'service': test_webpay_service(),
        'transaction': test_create_transaction()
    }
    
    print_section("RESUMEN DE RESULTADOS")
    
    for name, result in results.items():
        if result is True:
            print(f"✅ {name.upper()}: OK")
        elif result is False:
            print(f"❌ {name.upper()}: FALLÓ")
        else:
            print(f"⚠️ {name.upper()}: NO PROBADO")
    
    all_ok = all(r is True for r in results.values() if r is not None)
    
    print("\n" + "=" * 80)
    if all_ok:
        print("✅ ¡TODO CORRECTO! Webpay está listo para usar")
    else:
        print("❌ HAY PROBLEMAS QUE CORREGIR")
        print("\nPasos siguientes:")
        if not results['imports']:
            print("  1. Verifica que transbank-sdk esté instalado: pip install transbank-sdk==3.0.0")
        if not results['service']:
            print("  2. Revisa los logs de Django al iniciar el servidor")
            print("  3. Asegúrate de eliminar self.Transaction del __init__")
        if results['transaction'] is False:
            print("  4. Revisa el error específico en los logs arriba")
    print("=" * 80)

if __name__ == '__main__':
    main()

