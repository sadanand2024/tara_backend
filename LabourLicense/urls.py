from django.urls import path
from .views import *

urlpatterns = [
    # Entrepreneur Details
    path('entrepreneurs/', entrepreneur_details_list, name='entrepreneur-list'),
    path('entrepreneurs/<int:pk>/', entrepreneur_details_detail, name='entrepreneur-detail'),

    # Establishment Details
    path('establishments/', establishment_details_list, name='establishment-list'),
    path('establishments/<int:pk>/', establishment_details_detail, name='establishment-detail'),
    path('work-location/' ,work_location_list, name='work-location-list'),
    path('work-location/<int:pk>/', work_location_detail, name='work-location-detail'),


    # Employer Details
    path('employers/', employer_details_list, name='employer-list'),
    path('employers/<int:pk>/', employer_details_detail, name='employer-detail'),

    path('employers-file/', files_list, name='files-list'),
    path('employers-file/<int:pk>/', files_detail, name='files-detail'),
]
