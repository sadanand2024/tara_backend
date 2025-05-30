from django.contrib import admin
from django.urls import path, re_path
from django.conf.urls import include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from Tara.utils import *  # Custom utility imports
from django.conf import settings
from django.conf.urls.static import static

# Swagger schema view
schema_view = get_schema_view(
    openapi.Info(
        title="TARA Project API",
        default_version="v1",
        description="API documentation for your TARA project",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="mekalasaikiran0001@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Initial URL patterns
urlpatterns = [
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    # Swagger documentation URL
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # Redoc documentation URL
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    # Include user management URLs
    # path('user_management/', include('user_management.urls')),
    # Include Invoicing URLs
    path('invoicing/', include('invoicing.urls')),
    # Include Invoicing URLs
    path('payroll/', include('payroll.urls')),

    path('openapi.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),

    path('user_management/', include('usermanagement.urls')),

    path('companyincorporation/',include('company_incorporation.urls')),

    path('gst/', include('gst.urls')),

    path('labourlicense/', include('labour_license.urls')),

    path('servicetasks/', include('servicetasks.urls')),

    path('income_tax_returns/', include('income_tax_returns.urls')),

    path('msme/', include('msme_registration.urls')),

    path('docwallet/', include('docwallet.urls')),

    path('tradelicense/', include('trade_license.urls')),
    # Token authentication URL
    path('token_auth/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


