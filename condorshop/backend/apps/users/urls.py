from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from . import views

urlpatterns = [
    # Authentication endpoints
    path('register', views.register, name='register'),
    path('login', views.login, name='login'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('forgot-password', views.forgot_password, name='forgot_password'),
    path('password-reset', views.forgot_password, name='forgot_password_legacy'),
    path('reset-password', views.reset_password, name='reset_password'),
    path('password-reset/confirm', views.reset_password, name='reset_password_legacy'),
    path('verify-reset-token/<uuid:token>/', views.verify_reset_token, name='verify_reset_token'),
    # User profile endpoints
    path('profile', views.profile, name='profile'),
    path('me', views.deactivate_account, name='deactivate_account'),
    # Address endpoints
    path('addresses', views.addresses, name='addresses'),
    path('addresses/<int:address_id>', views.address_detail, name='address_detail'),
]

