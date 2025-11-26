"""
URLs para apps.common
"""
from django.urls import path
from . import views

app_name = 'common'

urlpatterns = [
    path('hero-carousel/', views.hero_carousel_slides, name='hero-carousel'),
]

