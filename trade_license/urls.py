from django.urls import path
from . import views

urlpatterns = [
    # Basic Details
    path('basic-details/', views.basic_details_list, name='basic_details_list'),
    path('basic-details/<int:pk>/', views.basic_detail, name='basic_detail'),

    # Trade License Exist
    path('trade-license-exist/', views.trade_license_exist_list, name='trade_license_exist_list'),
    path('trade-license-exist/<int:pk>/', views.trade_license_exist, name='trade_license_exist'),

    # Trade Entity
    path('trade-entity/', views.trade_entity_list, name='trade_entity_list'),
    path('trade-entity/<int:pk>/', views.trade_entity_detail, name='trade_entity_detail'),

    # Partner Details
    path('partner-details/', views.partner_details_list, name='partner_details_list'),
    path('partner-details/<int:pk>/', views.partner_details, name='partner_detail'),
]
