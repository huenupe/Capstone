"""
Script para corregir URLs de imágenes en la base de datos.

Este script convierte URLs mal formateadas a URLs relativas correctas
que Django puede servir bajo /media/
"""
from django.core.management.base import BaseCommand
from apps.products.models import ProductImage
import os
import re


class Command(BaseCommand):
    help = 'Corrige URLs de imágenes en product_images a formato relativo /media/productos/...'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Iniciando corrección de URLs de imágenes...'))
        
        updated_count = 0
        errors = []
        
        for img in ProductImage.objects.all():
            original_url = img.url
            new_url = self.fix_image_url(original_url)
            
            if new_url != original_url:
                try:
                    img.url = new_url
                    img.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Imagen ID {img.id}: "{original_url}" → "{new_url}"'
                        )
                    )
                except Exception as e:
                    error_msg = f'✗ Error al actualizar imagen ID {img.id}: {str(e)}'
                    errors.append(error_msg)
                    self.stdout.write(self.style.ERROR(error_msg))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Proceso completado: {updated_count} URLs corregidas'))
        
        if errors:
            self.stdout.write(self.style.ERROR(f'\n⚠️  {len(errors)} errores encontrados:'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f'  - {error}'))
    
    def fix_image_url(self, url):
        """
        Convierte diferentes formatos de URL a formato relativo /media/productos/...
        
        Formatos soportados:
        - file:///C:/Users/.../productos/archivo.webp → /media/productos/archivo.webp
        - backend\media\productos\archivo.webp → /media/productos/archivo.webp
        - backend/media/productos/archivo.webp → /media/productos/archivo.webp
        - /media/productos/archivo.webp → /media/productos/archivo.webp (ya correcto)
        """
        if not url:
            return url
        
        # Si ya está en formato correcto, retornar
        if url.startswith('/media/productos/'):
            return url
        
        # Extraer nombre del archivo de diferentes formatos
        filename = None
        
        # Caso 1: file:///C:/Users/.../productos/archivo.webp
        if url.startswith('file:///'):
            # Decodificar URL encoding
            try:
                from urllib.parse import unquote
                url_decoded = unquote(url)
                # Extraer nombre del archivo
                match = re.search(r'productos[/\\\\]([^/\\\\]+\\.(webp|jpg|jpeg|png|gif))', url_decoded, re.IGNORECASE)
                if match:
                    filename = match.group(1)
            except Exception:
                pass
        
        # Caso 2: backend\\media\\productos\\archivo.webp o backend/media/productos/archivo.webp
        if not filename:
            match = re.search(r'productos[/\\\\]([^/\\\\]+\\.(webp|jpg|jpeg|png|gif))', url, re.IGNORECASE)
            if match:
                filename = match.group(1)
        
        # Caso 3: Solo el nombre del archivo
        if not filename:
            match = re.search(r'([^/\\\\]+\\.(webp|jpg|jpeg|png|gif))$', url, re.IGNORECASE)
            if match:
                filename = match.group(1)
        
        # Si encontramos el nombre del archivo, construir URL correcta
        if filename:
            # Normalizar nombre del archivo (minúsculas, sin espacios)
            filename_normalized = filename.lower().replace(' ', '-')
            return f'/media/productos/{filename_normalized}'
        
        # Si no pudimos extraer el nombre, retornar URL original
        self.stdout.write(
            self.style.WARNING(f'⚠️  No se pudo extraer nombre de archivo de: {url}')
        )
        return url

