from django.urls import path
from .views import index, brand_details, kant_main

urlpatterns = [
    path('', index),
    path('kant/', kant_main, name = 'kant_main'),
    path('kant/<slug:brand>/', brand_details, name='brand_details'),
]
