from django.urls import path
from .views import *

urlpatterns = [
    # Entrepreneur Details
    path('basic-detail/', create_basic_details, name='basic-detail'),
    path('basic-detail/<int:pk>/', basic_details_view, name='basic-detail-view'),
    path('business-detail/', business_details_list, name='business-details-list'),
    path('business-detail/<int:pk>/', business_details_view, name='business-details-detail'),
    path('business-documents/', business_document_list_create, name='business-documents-list-create'),
    path('business-documents/<int:pk>/', business_document_detail, name='business-documents-detail'),
    path('partners/', partner_list, name='partner-list'),
    path('partners/<int:pk>/', partner_detail, name='partner-detail'),
    path('principal-place/', principal_place_list, name='principal_place_list'),
    path('principal-place/<int:pk>/', principal_place_detail_view, name='principal_place_detail'),
    ]