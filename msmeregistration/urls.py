from django.urls import path
from .views import *

urlpatterns = [
    path('msme/', msme_list, name='msme-list'),  # List and create MSME records
    path('msme/<int:pk>/', msme_detail, name='msme-detail'),  # Retrieve, update, delete MSME record
]
