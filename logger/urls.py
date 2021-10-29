from django.urls import path
from .views import index, brand_details, kant_main

urlpatterns = [
    path('', index, name='index'),
    path('kant/', kant_main, name='kant_main'),
    path('kant/<str:brand>/', brand_details, name='brand_details'),
]
