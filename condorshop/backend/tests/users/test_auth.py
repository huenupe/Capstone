import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone

from apps.users.models import PasswordResetToken


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


@pytest.mark.django_db
def test_forgot_password_creates_token_and_sends_email(api_client, user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

    response = api_client.post(
        "/api/auth/forgot-password",
        {"email": user.email},
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Si el email existe, recibirás instrucciones"
    assert mail.outbox  # Se envió correo

    token = PasswordResetToken.objects.filter(user=user).latest("created_at")
    assert token.is_valid()
    assert str(token.token) in mail.outbox[0].body


@pytest.mark.django_db
def test_reset_password_with_valid_token(api_client, user):
    token = PasswordResetToken.objects.create(user=user)

    response = api_client.post(
        "/api/auth/reset-password",
        {
            "token": str(token.token),
            "password": "NuevaClave123!",
            "password_confirm": "NuevaClave123!",
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Contraseña actualizada correctamente"

    user.refresh_from_db()
    assert user.check_password("NuevaClave123!")

    token.refresh_from_db()
    assert token.used_at is not None
    assert token.used_at <= timezone.now()


@pytest.mark.django_db
def test_verify_reset_token_invalid(api_client):
    response = api_client.get("/api/auth/verify-reset-token/00000000-0000-0000-0000-000000000000/")
    assert response.status_code == 400
    assert response.json()["error"] == "Token inválido o expirado"


