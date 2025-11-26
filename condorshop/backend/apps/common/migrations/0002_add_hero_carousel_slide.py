# Generated manually for HeroCarouselSlide model
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_create_store_config'),
    ]

    operations = [
        migrations.CreateModel(
            name='HeroCarouselSlide',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_column='name', help_text='Nombre descriptivo del slide (ej: "Ofertas de Verano")', max_length=100, verbose_name='Nombre')),
                ('description', models.TextField(blank=True, db_column='description', help_text='Descripción breve del slide (opcional)', max_length=500, null=True, verbose_name='Descripción')),
                ('image', models.ImageField(db_column='image', help_text='Imagen del slide. Se recomienda formato 1920x480px o similar (relación 4:1)', upload_to='hero_carousel/', verbose_name='Imagen')),
                ('alt_text', models.CharField(db_column='alt_text', help_text='Texto alternativo para accesibilidad (usado como alt de la imagen)', max_length=200, verbose_name='Texto alternativo')),
                ('order', models.PositiveIntegerField(db_column='order', default=0, help_text='Orden de visualización (menor número = aparece primero)', verbose_name='Orden')),
                ('is_active', models.BooleanField(db_column='is_active', default=True, help_text='Si está desactivado, no se mostrará en el carrusel', verbose_name='Activo')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='Creado el')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='updated_at', verbose_name='Actualizado el')),
            ],
            options={
                'verbose_name': 'Slide del Carrusel',
                'verbose_name_plural': 'Slides del Carrusel',
                'db_table': 'hero_carousel_slides',
                'ordering': ['order', 'created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='herocarouselslide',
            index=models.Index(fields=['is_active', 'order'], name='idx_hero_slide_active_order'),
        ),
        migrations.AddIndex(
            model_name='herocarouselslide',
            index=models.Index(fields=['created_at'], name='idx_hero_slide_created'),
        ),
    ]

