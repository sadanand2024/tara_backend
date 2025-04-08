from django.urls import path
from .views import *

urlpatterns = [
    path('companies/', get_all_companies, name='get_all_companies'),  # GET all companies
    path('company/create/', create_company, name='create_company'),  # POST to create company
    path('company/<str:id>/', company_detail, name='company_detail'),  # GET, PUT, DELETE by ID

    path('authorized-capital/', authorized_capital_list_create, name='authorized_capital_list_create'),
    path('authorized-capital/<int:pk>/', authorized_capital_detail, name='authorized_capital_detail'),

    path('share-holders/', share_holders_list_create, name='share_holders_list_create'),
    path('share-holders/<int:pk>/', shareholder_detail, name='share_holders_detail'),

        path('directors-details/', directors_details, name='directors_details'),
    path('directors-details/<int:pk>/',directors_details_update,name='directors_detail'),

    path('existing-company/', existing_company, name='directors_details'),
    path('existing-company/<int:pk>/', existing_company_detail, name='directors_detail')
]
