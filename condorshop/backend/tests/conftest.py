import pytest
from rest_framework.test import APIClient

from apps.orders.models import OrderStatus
from tests.factories import OrderStatusFactory, UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def pending_status():
    return OrderStatus.objects.get_or_create(code="PENDING", defaults={"description": "Pendiente"})[0]


