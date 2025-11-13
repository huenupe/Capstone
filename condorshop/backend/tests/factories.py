import factory
from django.contrib.auth import get_user_model

from apps.cart.models import Cart, CartItem
from apps.orders.models import OrderStatus
from apps.products.models import Category, Product


class UserFactory(factory.django.DjangoModelFactory):
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    role = "cliente"

    class Meta:
        model = get_user_model()
        skip_postgeneration_save = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        password = extracted or "Password123!"
        self.set_password(password)
        if create:
            self.save()


class CategoryFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.Sequence(lambda n: f"category-{n}")
    description = factory.Faker("sentence")

    class Meta:
        model = Category


class ProductFactory(factory.django.DjangoModelFactory):
    category = factory.SubFactory(CategoryFactory)
    name = factory.Sequence(lambda n: f"Product {n}")
    slug = factory.Sequence(lambda n: f"product-{n}")
    price = 19990
    stock_qty = 10
    sku = factory.Sequence(lambda n: f"SKU{n:05d}")
    active = True

    class Meta:
        model = Product


class OrderStatusFactory(factory.django.DjangoModelFactory):
    code = factory.Sequence(lambda n: f"STATUS_{n}")
    description = factory.Faker("sentence")

    class Meta:
        model = OrderStatus


class CartFactory(factory.django.DjangoModelFactory):
    user = None
    session_token = factory.Faker("uuid4")
    is_active = True

    class Meta:
        model = Cart


class CartItemFactory(factory.django.DjangoModelFactory):
    cart = factory.SubFactory(CartFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = 1
    unit_price = factory.LazyAttribute(lambda obj: obj.product.final_price)
    total_price = factory.LazyAttribute(lambda obj: obj.unit_price * obj.quantity)

    class Meta:
        model = CartItem


