# Generated manually for Acción 5: Completar jerarquía de categorías
from django.db import migrations, models


def populate_level_and_set_defaults(apps, schema_editor):
    """
    Poblar level basado en parent_category y establecer defaults para sort_order y active.
    """
    Category = apps.get_model('products', 'Category')
    
    def calculate_level(category, visited=None):
        """Calcular level recursivamente"""
        if visited is None:
            visited = set()
        
        if category.pk in visited:
            return 0  # Evitar ciclos
        
        visited.add(category.pk)
        
        if category.parent_category_id:
            parent = Category.objects.get(pk=category.parent_category_id)
            return calculate_level(parent, visited) + 1
        return 0
    
    # Calcular y actualizar level para todas las categorías
    for category in Category.objects.all():
        category.level = calculate_level(category)
        if not hasattr(category, 'sort_order') or category.sort_order is None:
            category.sort_order = 0
        if not hasattr(category, 'active') or category.active is None:
            category.active = True
        Category.objects.filter(pk=category.pk).update(
            level=category.level,
            sort_order=category.sort_order,
            active=category.active
        )


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0008_populate_initial_price_history'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='level',
            field=models.SmallIntegerField(
                default=0,
                editable=False,
                db_column='level',
                verbose_name='Nivel',
                help_text='Nivel en la jerarquía (0 = raíz, calculado automáticamente)'
            ),
        ),
        migrations.AddField(
            model_name='category',
            name='sort_order',
            field=models.IntegerField(
                default=0,
                db_column='sort_order',
                verbose_name='Orden',
                help_text='Orden de visualización (menor = primero)'
            ),
        ),
        migrations.AddField(
            model_name='category',
            name='active',
            field=models.BooleanField(
                default=True,
                db_column='active',
                verbose_name='Activa',
                help_text='Indica si la categoría está activa y visible'
            ),
        ),
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['parent_category', 'active'], name='idx_category_parent_active'),
        ),
        migrations.AlterModelOptions(
            name='category',
            options={
                'verbose_name': 'Categoría',
                'verbose_name_plural': 'Categorías',
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.RunPython(
            populate_level_and_set_defaults,
            reverse_code=migrations.RunPython.noop
        ),
    ]

