from django.urls import path
from . import views

urlpatterns = [
    # BasicBusinessInfo
    path('basic-business-info/', views.basic_business_info_list_create, name='basic_business_info_list_create'),
    path('basic-business-info/by-service-request/', views.basic_business_info_by_service_request, name='basic_business_info_by_service_request'),
    path('basic-business-info/<int:pk>/', views.basic_business_info_detail, name='basic_business_info_detail'),

    # RegistrationInfo
    path('registration-info/', views.registration_info_list_create, name='registration_info_list_create'),
    path('registration-info/by-service-request/', views.registration_info_by_service_request, name='registration_info_by_service_request'),
    path('registration-info/<int:pk>/', views.registration_info_detail, name='registration_info_detail'),

    # PrincipalPlaceDetails
    path('principal-place-details/', views.principal_place_details_list_create, name='principal_place_details_list_create'),
    path('principal-place-details/by-service-request/', views.principal_place_details_by_service_request, name='principal_place_details_by_service_request'),
    path('principal-place-details/<int:pk>/', views.principal_place_details_detail, name='principal_place_details_detail'),

    # PromoterSignatoryDetails
    path('promoter-signatory-details/', views.promoter_signatory_details_create,
         name='promoter_signatory_details_create'),
    path('promoter-signatory-details/by-service-request', views.promoter_signatory_details_get,
         name='promoter_signatory_details_get'),

    # PromoterSignatoryInfo
    path('promoter-signatory-info/', views.promoter_signatory_info_create,
         name='promoter_signatory_info_create'),
    path('promoter-signatory-info/<int:pk>/', views.promoter_signatory_info_update,
         name='promoter_signatory_info_update'),
    path('promoter-signatory-info/by-service-request/', views.promoter_signatory_info_get, name='promoter_signatory_info_get'),

    path('promoter-signatory-info/<int:pk>/delete/', views.promoter_signatory_info_delete, name='promoter_signatory_info_delete'),

# GSTReviewFilingCertificate
    path('gst-review-filing-certificate/', views.gst_review_filing_certificate_list_create, name='gst_review_filing_certificate_list_create'),
    path('gst-review-filing-certificate/by-service-request/', views.gst_review_filing_certificate_by_service_request, name='gst_review_filing_certificate_by_service_request'),
    path('gst-review-filing-certificate/<int:pk>/', views.gst_review_filing_certificate_detail, name='gst_review_filing_certificate_detail'),
]