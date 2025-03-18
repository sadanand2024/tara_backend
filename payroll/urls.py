from django.urls import path
from . import views

urlpatterns = [
    # URL for listing and creating PayrollOrg instances
    path('orgs/', views.PayrollOrgList.as_view(), name='payroll_org_list'),

    # URL for retrieving, updating, or deleting a specific PayrollOrg by its ID
    path('orgs/<int:pk>/', views.PayrollOrgDetail.as_view(), name='payroll_org_detail'),

    # URL for retrieving, updating, or deleting a specific PayrollOrg by its ID
    path('update-payroll-org/<int:business_id>/', views.update_payroll_org, name='update_payroll_org'),

    # path('business-payroll/<int:business_id>/', views.PayrollOrgBusinessDetail.as_view(), name='payroll-org-detail'),

    path('business-payroll/<int:business_id>/', views.PayrollOrgBusinessDetailView.as_view(),
         name='payroll-org-business-detail'),

    path('payroll-setup-status', views.business_payroll_check, name='business_payroll_check'),

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

    path('epf', views.epf_list, name='epf_list'),
    path('epf/<int:pk>', views.epf_detail, name='epf_detail'),

    # ESI Endpoints
    path('esi', views.esi_list, name='esi_list'),
    path('esi/<int:pk>', views.esi_detail, name='esi_detail'),

    # URL for listing and creating PF records
    path('pt', views.pt_list, name='pf_list'),

    # URL for retrieving, updating, or deleting a specific PF record by its ID
    path('pt/<int:pk>', views.pt_detail, name='pf_detail'),

    # URL for listing and creating Earnings records

    path('earnings', views.earnings_list, name='earnings_list'),

    # URL for retrieving, updating, or deleting a specific Earnings record by its ID
    path('earnings/<int:pk>', views.earnings_detail, name='earnings_detail'),

    path('deductions/', views.deduction_list_create, name='deduction-list-create'),
    path('deductions/<int:id>/', views.deduction_detail, name='deduction-detail'),

    # Reimbursement Endpoints
    path('reimbursements/', views.reimbursement_list_create, name='reimbursement-list-create'),
    path('reimbursements/<int:id>/', views.reimbursement_detail, name='reimbursement-detail'),

    # Benefit Endpoints
    path('benefits/', views.benefits_list_create, name='benefit-list-create'),
    path('benefits/<int:id>/', views.benefits_detail_update_delete, name='benefit-detail'),

    # Salary Template Endpoints
    path('salary-templates', views.salary_template_list_create, name='salary_template_list_create'),
    path('salary-templates/<int:template_id>', views.salary_template_detail_update_delete,
         name='salary_template_detail_update_delete'),

    # pay-schedules Endpoints
    path('pay-schedules',  views.pay_schedule_list_create, name='pay_schedule_list_create'),
    path('pay-schedules/<int:schedule_id>',  views.pay_schedule_detail_update_delete,
         name='pay_schedule_detail_update_delete'),

    path('leave-management', views.leave_management_list_create, name='leave-management-list-create'),
    path('leave-management/<int:leave_id>', views.leave_management_detail_update_delete,
         name='leave-management-detail-update-delete'),

    # Holiday Management URLs
    path('holiday-management', views.holiday_management_list_create, name='holiday-management-list-create'),
    path('holiday-management-filter', views.holiday_management_filtered_list, name='holiday-management-filtered-list'),
    path('holiday-management/<int:holiday_id>', views.holiday_management_detail_update_delete,
         name='holiday-management-detail-update-delete'),

    path('employees', views.employee_list, name='employee-list'),
    path('employees/<int:pk>', views.employee_detail, name='employee-detail'),

    path('employee-salary', views.employee_salary_list, name='employee-salary-list'),
    path('employee-salary/<int:pk>', views.employee_salary_detail, name='employee-salary-detail'),

    path('employee-personal-details', views.employee_personal_list, name='employee-personal-list'),
    path('employee-personal-details/<int:pk>', views.employee_personal_detail, name='employee-personal-detail'),

    path('employee-bank-details', views.employee_bank_list, name='employee-bank-list'),
    path('employee-bank-details/<int:pk>', views.employee_bank_detail, name='employee-bank-detail'),

    path('salary-benefits-details/<int:payroll_id>', views.get_payroll_details, name='payroll-details'),

]
