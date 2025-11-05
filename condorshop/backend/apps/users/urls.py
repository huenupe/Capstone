from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from . import views

urlpatterns = [
    # Authentication endpoints
    path('register', views.register, name='register'),
    path('login', views.login, name='login'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # User profile endpoints
    path('profile', views.profile, name='profile'),
]

