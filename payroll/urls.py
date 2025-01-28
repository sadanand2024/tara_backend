from django.urls import path
from . import views

urlpatterns = [
    # URL for listing and creating PayrollOrg instances
    path('orgs/', views.PayrollOrgList.as_view(), name='payroll_org_list'),

    # URL for retrieving, updating, or deleting a specific PayrollOrg by its ID
    path('orgs/<int:pk>/', views.PayrollOrgDetail.as_view(), name='payroll_org_detail'),

    # URL for listing and creating WorkLocation instances
    path('work-locations/', views.work_location_list, name='work_location_list'),

    path('work-locations/bulk-upload/', views.bulk_work_location_upload, name='bulk_work_location_upload'),

    # URL for creating a new WorkLocation
    path('work-locations/create/', views.work_location_create, name='work_location_create'),

    # URL for retrieving, updating, or deleting a specific WorkLocation by its ID
    path('work-locations/<int:pk>/', views.work_location_detail, name='work_location_detail'),

    # URL for updating a specific WorkLocation by its ID
    path('work-locations/update/<int:pk>/', views.work_location_update, name='work_location_update'),

    # URL for deleting a specific WorkLocation by its ID
    path('work-locations/delete/<int:pk>/', views.work_location_delete, name='work_location_delete'),

    # URL for listing and creating Department instances
    path('departments/', views.department_list, name='department_list'),

    # URL for retrieving, updating, or deleting a specific Department by its ID
    path('departments/<int:pk>/', views.department_detail, name='department_detail'),

    path('departments/bulk-department-upload/', views.bulk_department_upload, name='bulk_department_upload'),


    # URL for listing and creating Designation instances
    path('designations/', views.designation_list, name='designation_list'),

    # URL for retrieving, updating, or deleting a specific Designation by its ID
    path('designations/<int:pk>/', views.designation_detail, name='designation_detail'),

    path('designations/bulk-designations-upload/', views.bulk_designation_upload, name='bulk_designation_upload'),

    path('epf/', views.epf_list, name='epf_list'),
    path('epf/<int:pk>/', views.epf_detail, name='epf_detail'),

    # ESI Endpoints
    path('esi/', views.esi_list, name='esi_list'),
    path('esi/<int:pk>/', views.esi_detail, name='esi_detail'),

    # URL for listing and creating PF records
    path('pf/', views.pf_list, name='pf_list'),

    # URL for retrieving, updating, or deleting a specific PF record by its ID
    path('pf/<int:pk>/', views.pf_detail, name='pf_detail'),

    # URL for listing and creating Earnings records
    path('earnings/', views.earnings_list, name='earnings_list'),

    # URL for retrieving, updating, or deleting a specific Earnings record by its ID
    path('earnings/<int:pk>/', views.earnings_detail, name='earnings_detail'),


    path('deductions/', views.deduction_list_create, name='deduction-list-create'),
    path('deductions/<int:id>/', views.deduction_detail, name='deduction-detail'),

    # Reimbursement Endpoints
    path('reimbursements/', views.reimbursement_list_create, name='reimbursement-list-create'),
    path('reimbursements/<int:id>/', views.reimbursement_detail, name='reimbursement-detail'),

    # Benefit Endpoints
    path('benefits/', views.benefits_list_create, name='benefit-list-create'),
    path('benefits/<int:id>/', views.benefits_detail_update_delete, name='benefit-detail'),


]
