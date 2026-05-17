"""
URL configuration for pharmacy_inventory project.
"""
from django.urls import path, include

urlpatterns = [
    path('', include('pharmacy.urls')),
]