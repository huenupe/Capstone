import pytest
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_register_creates_user_and_returns_tokens(api_client):
    payload = {
        "email": "newuser@example.com",
        "first_name": "New",
        "last_name": "User",
        "phone": "+56912345678",
        "password": "StrongPass123!",
        "password_confirm": "StrongPass123!",
    }

    response = api_client.post("/api/auth/register", payload, format="json")

    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == payload["email"]
    assert "access" in data["tokens"]
    assert "refresh" in data["tokens"]

    user = get_user_model().objects.get(email=payload["email"])
    assert user.check_password(payload["password"])


@pytest.mark.django_db
def test_login_returns_tokens_for_valid_credentials(api_client, user):
    response = api_client.post(
        "/api/auth/login",
        {"email": user.email, "password": "Password123!"},
        format="json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == user.email
    assert "access" in data["tokens"]
    assert "refresh" in data["tokens"]


@pytest.mark.django_db
def test_login_rejects_invalid_credentials(api_client, user):
    response = api_client.post(
        "/api/auth/login",
        {"email": user.email, "password": "WrongPassword!"},
        format="json",
    )

    assert response.status_code == 401
    assert response.json()["error"] == "Credenciales inválidas"


