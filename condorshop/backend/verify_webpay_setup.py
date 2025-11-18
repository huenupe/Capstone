#!/usr/bin/env python
"""
Script de verificación de configuración Webpay Plus
Ejecutar antes de iniciar las pruebas: python verify_webpay_setup.py
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'condorshop_api.settings')
django.setup()

from django.conf import settings
from apps.orders.services import webpay_service, TRANSBANK_AVAILABLE

def verify_webpay_setup():
    """Verifica que la configuración de Webpay esté correcta"""
    print("=" * 60)
    print("VERIFICACIÓN DE CONFIGURACIÓN WEBPAY PLUS")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # 1. Verificar transbank-sdk
    print("\n1. Verificando transbank-sdk...")
    if TRANSBANK_AVAILABLE:
        print("   [OK] transbank-sdk esta instalado")
    else:
        errors.append("transbank-sdk NO esta instalado. Ejecuta: pip install transbank-sdk")
        print("   [ERROR] transbank-sdk NO esta instalado")
    
    # 2. Verificar webpay_service
    print("\n2. Verificando WebpayService...")
    if webpay_service is not None:
        print("   [OK] WebpayService esta disponible")
    else:
        errors.append("WebpayService no esta disponible")
        print("   [ERROR] WebpayService no esta disponible")
    
    # 3. Verificar configuración
    print("\n3. Verificando configuración...")
    config = settings.WEBPAY_CONFIG
    
    print(f"   ENVIRONMENT: {config['ENVIRONMENT']}")
    if config['ENVIRONMENT'] not in ['integration', 'production']:
        errors.append(f"ENVIRONMENT debe ser 'integration' o 'production', actual: {config['ENVIRONMENT']}")
    
    print(f"   COMMERCE_CODE: {config['COMMERCE_CODE']}")
    if not config['COMMERCE_CODE']:
        errors.append("COMMERCE_CODE no está configurado")
    
    print(f"   API_KEY: {'***' + config['API_KEY'][-4:] if config['API_KEY'] else 'NO CONFIGURADO'}")
    if not config['API_KEY']:
        errors.append("API_KEY no está configurado")
    
    print(f"   RETURN_URL: {config['RETURN_URL']}")
    if not config['RETURN_URL']:
        errors.append("RETURN_URL no está configurado")
    elif config['ENVIRONMENT'] == 'production' and 'localhost' in config['RETURN_URL']:
        errors.append("RETURN_URL no puede usar localhost en producción")
    
    print(f"   FINAL_URL: {config['FINAL_URL']}")
    if not config['FINAL_URL']:
        errors.append("FINAL_URL no está configurado")
    elif config['ENVIRONMENT'] == 'production' and 'localhost' in config['FINAL_URL']:
        errors.append("FINAL_URL no puede usar localhost en producción")
    
    # 4. Verificar URLs del frontend
    print("\n4. Verificando URLs del frontend...")
    frontend_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', '.env')
    if os.path.exists(frontend_env):
        with open(frontend_env, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'VITE_WEBPAY_ENABLED=true' in content:
                print("   [OK] VITE_WEBPAY_ENABLED esta configurado")
            else:
                warnings.append("VITE_WEBPAY_ENABLED no esta en 'true' en frontend/.env")
                print("   [ADVERTENCIA] VITE_WEBPAY_ENABLED no esta configurado como 'true'")
    else:
        warnings.append("frontend/.env no encontrado")
        print("   [ADVERTENCIA] frontend/.env no encontrado")
    
    # 5. Verificar modelos
    print("\n5. Verificando modelos...")
    from apps.orders.models import Order, Payment, PaymentTransaction, OrderStatus, PaymentStatus
    
    # Verificar estados necesarios
    required_statuses = ['PENDING', 'PAID', 'FAILED']
    for status_code in required_statuses:
        try:
            OrderStatus.objects.get(code=status_code)
            print(f"   [OK] OrderStatus '{status_code}' existe")
        except OrderStatus.DoesNotExist:
            errors.append(f"OrderStatus '{status_code}' no existe en la base de datos")
            print(f"   [ERROR] OrderStatus '{status_code}' NO existe")
    
    required_payment_statuses = ['CREATED', 'CAPTURED', 'FAILED']
    for status_code in required_payment_statuses:
        try:
            PaymentStatus.objects.get(code=status_code)
            print(f"   [OK] PaymentStatus '{status_code}' existe")
        except PaymentStatus.DoesNotExist:
            errors.append(f"PaymentStatus '{status_code}' no existe en la base de datos")
            print(f"   [ERROR] PaymentStatus '{status_code}' NO existe")
    
    # Resumen
    print("\n" + "=" * 60)
    if errors:
        print("[ERROR] ERRORES ENCONTRADOS:")
        for error in errors:
            print(f"   - {error}")
        print("\n[ADVERTENCIA] Corrige estos errores antes de continuar con las pruebas.")
        return False
    else:
        print("[OK] CONFIGURACION CORRECTA")
        if warnings:
            print("\n[ADVERTENCIA] ADVERTENCIAS:")
            for warning in warnings:
                print(f"   - {warning}")
        print("\n[OK] Todo esta listo para iniciar las pruebas de Webpay Plus.")
        return True

if __name__ == '__main__':
    success = verify_webpay_setup()
    sys.exit(0 if success else 1)

