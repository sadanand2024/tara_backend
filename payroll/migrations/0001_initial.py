# Generated by Django 5.0.4 on 2025-06-26 14:57

import django.db.models.deletion
import payroll.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('usermanagement', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Departments',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dept_code', models.CharField(max_length=150)),
                ('dept_name', models.CharField(max_length=150)),
                ('description', models.CharField(blank=True, max_length=220, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Designation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('designation_name', models.CharField(max_length=150)),
            ],
        ),
        migrations.CreateModel(
            name='LeaveManagement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_of_leave', models.CharField(max_length=120)),
                ('code', models.CharField(blank=True, default=None, max_length=20, null=True)),
                ('leave_type', models.CharField(max_length=60)),
                ('employee_leave_period', models.CharField(default='-', max_length=80)),
                ('number_of_leaves', models.FloatField(blank=True, default=None, null=True)),
                ('pro_rate_leave_balance_of_new_joinees_based_on_doj', models.BooleanField(default=False)),
                ('reset_leave_balance', models.BooleanField(default=False)),
                ('reset_leave_balance_type', models.CharField(default=None, max_length=20, null=True)),
                ('carry_forward_unused_leaves', models.BooleanField(default=False)),
                ('max_carry_forward_days', models.IntegerField(default=None, null=True)),
                ('encash_remaining_leaves', models.BooleanField(default=False)),
                ('encashment_days', models.IntegerField(default=None, null=True)),
            ],
            options={
                'verbose_name': 'Leave Management',
                'verbose_name_plural': 'Leave Managements',
            },
        ),
        migrations.CreateModel(
            name='EmployeeManagement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('createdAt', models.DateTimeField(auto_now_add=True)),
                ('updatedAt', models.DateTimeField(auto_now=True)),
                ('first_name', models.CharField(max_length=120)),
                ('middle_name', models.CharField(blank=True, default=None, max_length=80, null=True)),
                ('last_name', models.CharField(max_length=80)),
                ('associate_id', models.CharField(max_length=120)),
                ('doj', models.DateField()),
                ('work_email', models.EmailField(max_length=254)),
                ('mobile_number', models.CharField(blank=True, max_length=20, null=True)),
                ('gender', models.CharField(choices=[('male', 'male'), ('female', 'female'), ('others', 'others')], default='male', max_length=20)),
                ('enable_portal_access', models.BooleanField(default=False)),
                ('statutory_components', models.JSONField()),
                ('employee_status', models.BooleanField(default=True)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_department', to='payroll.departments')),
                ('designation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_designation', to='payroll.designation')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EmployeeExit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doe', models.DateField()),
                ('exit_month', models.IntegerField(editable=False, null=True)),
                ('exit_year', models.IntegerField(editable=False, null=True)),
                ('exit_reason', models.CharField(blank=True, default=None, max_length=256, null=True)),
                ('regular_pay_schedule', models.BooleanField()),
                ('specify_date', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, default='', null=True)),
                ('employee', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='employee_exit_details', to='payroll.employeemanagement')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeBankDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('createdAt', models.DateTimeField(auto_now_add=True)),
                ('updatedAt', models.DateTimeField(auto_now=True)),
                ('account_holder_name', models.CharField(max_length=150)),
                ('bank_name', models.CharField(max_length=150)),
                ('account_number', models.CharField(max_length=20, unique=True)),
                ('ifsc_code', models.CharField(max_length=20)),
                ('branch_name', models.CharField(blank=True, max_length=150, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('employee', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='employee_bank_details', to='payroll.employeemanagement')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EmployeeAttendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('financial_year', models.CharField(max_length=10)),
                ('month', models.IntegerField()),
                ('total_days_of_month', models.IntegerField()),
                ('holidays', models.FloatField()),
                ('week_offs', models.IntegerField()),
                ('present_days', models.FloatField()),
                ('balance_days', models.FloatField()),
                ('casual_leaves', models.FloatField()),
                ('sick_leaves', models.FloatField()),
                ('earned_leaves', models.FloatField()),
                ('loss_of_pay', models.FloatField()),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_attendance', to='payroll.employeemanagement')),
            ],
        ),
        migrations.CreateModel(
            name='BonusIncentive',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bonus_type', models.CharField(max_length=120)),
                ('amount', models.IntegerField()),
                ('month', models.IntegerField()),
                ('year', models.IntegerField(editable=False)),
                ('financial_year', models.CharField(max_length=10)),
                ('remarks', models.TextField(blank=True, default='', null=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_bonus_incentive', to='payroll.employeemanagement')),
            ],
        ),
        migrations.CreateModel(
            name='AdvanceLoan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loan_type', models.CharField(max_length=120)),
                ('amount', models.IntegerField()),
                ('no_of_months', models.IntegerField()),
                ('emi_amount', models.IntegerField(editable=False)),
                ('start_month', models.DateField()),
                ('end_month', models.DateField(editable=False)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_advance_loan', to='payroll.employeemanagement')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeePersonalDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('createdAt', models.DateTimeField(auto_now_add=True)),
                ('updatedAt', models.DateTimeField(auto_now=True)),
                ('dob', models.DateField()),
                ('age', models.IntegerField()),
                ('guardian_name', models.CharField(max_length=120)),
                ('pan', models.CharField(default=None, max_length=20, null=True)),
                ('aadhar', models.CharField(default=None, max_length=80, null=True)),
                ('address', models.JSONField()),
                ('alternate_contact_number', models.CharField(blank=True, default=None, max_length=40, null=True)),
                ('marital_status', models.CharField(choices=[('single', 'single'), ('married', 'married')], default='single', max_length=20)),
                ('blood_group', models.CharField(choices=[('A+', 'A Positive (A+)'), ('A-', 'A Negative (A-)'), ('B+', 'B Positive (B+)'), ('B-', 'B Negative (B-)'), ('AB+', 'AB Positive (AB+)'), ('AB-', 'AB Negative (AB-)'), ('O+', 'O Positive (O+)'), ('O-', 'O Negative (O-)')], default='O+', max_length=3)),
                ('employee', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='employee_personal_details', to='payroll.employeemanagement')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EmployeeSalaryDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('annual_ctc', models.IntegerField()),
                ('earnings', models.JSONField(blank=True, default=list)),
                ('gross_salary', models.JSONField(blank=True, default=dict)),
                ('benefits', models.JSONField(blank=True, default=list)),
                ('total_ctc', models.JSONField(blank=True, default=dict)),
                ('deductions', models.JSONField(blank=True, default=list)),
                ('net_salary', models.JSONField(blank=True, default=dict)),
                ('tax_regime_opted', models.CharField(blank=True, default='new', max_length=225, null=True)),
                ('valid_from', models.DateField(auto_now_add=True)),
                ('valid_to', models.DateField(blank=True, null=True)),
                ('created_on', models.DateField(auto_now_add=True)),
                ('created_month', models.IntegerField(editable=False)),
                ('created_year', models.IntegerField(editable=False)),
                ('employee', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='employee_salary', to='payroll.employeemanagement')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeSalaryRevisionHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('previous_ctc', models.IntegerField()),
                ('current_ctc', models.IntegerField()),
                ('revision_date', models.DateField(blank=True, null=True)),
                ('revision_month', models.IntegerField(blank=True, null=True)),
                ('revision_year', models.IntegerField(blank=True, null=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='salary_revision_history', to='payroll.employeemanagement')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeLeaveBalance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('leave_entitled', models.FloatField()),
                ('leave_used', models.FloatField(default=0)),
                ('leave_remaining', models.FloatField()),
                ('financial_year', models.CharField(max_length=10)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leave_balances', to='payroll.employeemanagement')),
                ('leave_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leave_balances', to='payroll.leavemanagement')),
            ],
        ),
        migrations.CreateModel(
            name='PayrollOrg',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sender_email', models.EmailField(blank=True, max_length=120, null=True)),
                ('filling_address_location_name', models.CharField(blank=True, default='Head Office', max_length=120, null=True)),
                ('filling_address_line1', models.CharField(blank=True, max_length=150, null=True)),
                ('filling_address_line2', models.CharField(blank=True, max_length=150, null=True)),
                ('filling_address_state', models.CharField(blank=True, max_length=150, null=True)),
                ('filling_address_city', models.CharField(blank=True, max_length=150, null=True)),
                ('filling_address_pincode', models.PositiveIntegerField(null=True, validators=[payroll.models.validate_pincode])),
                ('work_location', models.BooleanField(default=False)),
                ('department', models.BooleanField(default=False)),
                ('designation', models.BooleanField(default=False)),
                ('statutory_component', models.BooleanField(default=False)),
                ('salary_component', models.BooleanField(default=False)),
                ('salary_template', models.BooleanField(default=False)),
                ('pay_schedule', models.BooleanField(default=False)),
                ('leave_management', models.BooleanField(default=False)),
                ('holiday_management', models.BooleanField(default=False)),
                ('employee_master', models.BooleanField(default=False)),
                ('business', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='usermanagement.business')),
            ],
        ),
        migrations.AddField(
            model_name='leavemanagement',
            name='payroll',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leave_managements', to='payroll.payrollorg'),
        ),
        migrations.CreateModel(
            name='HolidayManagement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('financial_year', models.CharField(max_length=20)),
                ('holiday_name', models.CharField(max_length=120)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('description', models.TextField(blank=True, null=True)),
                ('applicable_for', models.CharField(max_length=60)),
                ('payroll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='holiday_managements', to='payroll.payrollorg')),
            ],
            options={
                'verbose_name': 'Holiday Management',
                'verbose_name_plural': 'Holiday Managements',
            },
        ),
        migrations.CreateModel(
            name='ESI',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('esi_number', models.CharField(max_length=100)),
                ('employee_contribution', models.DecimalField(decimal_places=2, max_digits=5)),
                ('employer_contribution', models.DecimalField(decimal_places=2, max_digits=5)),
                ('include_employer_contribution_in_ctc', models.BooleanField()),
                ('is_disabled', models.BooleanField(default=False)),
                ('payroll', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='esi_details', to='payroll.payrollorg')),
            ],
        ),
        migrations.CreateModel(
            name='EPF',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('epf_number', models.CharField(max_length=100)),
                ('employee_contribution_rate', models.CharField(max_length=240)),
                ('employer_contribution_rate', models.CharField(max_length=240)),
                ('employer_edil_contribution_in_ctc', models.BooleanField()),
                ('include_employer_contribution_in_ctc', models.BooleanField()),
                ('admin_charge_in_ctc', models.BooleanField()),
                ('allow_employee_level_override', models.BooleanField()),
                ('prorate_restricted_pf_wage', models.BooleanField()),
                ('apply_components_if_wage_below_15k', models.BooleanField()),
                ('is_disabled', models.BooleanField(default=False)),
                ('payroll', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='epf_details', to='payroll.payrollorg')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeSalaryHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.IntegerField()),
                ('financial_year', models.CharField(max_length=10)),
                ('total_days_of_month', models.IntegerField()),
                ('lop', models.FloatField()),
                ('paid_days', models.FloatField()),
                ('ctc', models.IntegerField()),
                ('gross_salary', models.IntegerField()),
                ('earned_salary', models.IntegerField()),
                ('basic_salary', models.IntegerField()),
                ('hra', models.IntegerField()),
                ('special_allowance', models.IntegerField()),
                ('bonus', models.IntegerField()),
                ('other_earnings', models.IntegerField()),
                ('benefits_total', models.IntegerField()),
                ('epf', models.FloatField()),
                ('esi', models.FloatField()),
                ('pt', models.FloatField()),
                ('tds', models.FloatField()),
                ('tds_ytd', models.FloatField()),
                ('annual_tds', models.FloatField()),
                ('loan_emi', models.FloatField()),
                ('other_deductions', models.FloatField()),
                ('total_deductions', models.FloatField()),
                ('net_salary', models.IntegerField()),
                ('is_active', models.BooleanField(default=True)),
                ('change_date', models.DateField(auto_now_add=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_salary_history', to='payroll.employeemanagement')),
                ('payroll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payroll_employee_dashboard', to='payroll.payrollorg')),
            ],
        ),
        migrations.AddField(
            model_name='employeemanagement',
            name='payroll',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_managements', to='payroll.payrollorg'),
        ),
        migrations.CreateModel(
            name='Earnings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('component_name', models.CharField(max_length=150)),
                ('component_type', models.CharField(max_length=60)),
                ('calculation_type', models.JSONField(default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('is_part_of_employee_salary_structure', models.BooleanField(default=False)),
                ('is_taxable', models.BooleanField(default=True)),
                ('is_pro_rate_basis', models.BooleanField(default=False)),
                ('is_fbp_component', models.BooleanField(default=False)),
                ('includes_epf_contribution', models.BooleanField(default=False)),
                ('includes_esi_contribution', models.BooleanField(default=False)),
                ('is_included_in_payslip', models.BooleanField(default=True)),
                ('tax_deduction_preference', models.CharField(blank=True, max_length=120, null=True)),
                ('is_scheduled_earning', models.BooleanField(default=True)),
                ('pf_wage_less_than_15k', models.BooleanField(default=False)),
                ('always_consider_epf_inclusion', models.BooleanField(default=False)),
                ('payroll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='earnings', to='payroll.payrollorg')),
            ],
        ),
        migrations.AddField(
            model_name='designation',
            name='payroll',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='designations', to='payroll.payrollorg'),
        ),
        migrations.AddField(
            model_name='departments',
            name='payroll',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='departments', to='payroll.payrollorg'),
        ),
        migrations.CreateModel(
            name='Deduction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deduction_type', models.CharField(max_length=150)),
                ('payslip_name', models.CharField(max_length=60, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('frequency', models.CharField(max_length=120)),
                ('payroll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deductions', to='payroll.payrollorg')),
            ],
        ),
        migrations.CreateModel(
            name='Benefits',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('benefit_type', models.CharField(max_length=150)),
                ('associated_with', models.CharField(max_length=60)),
                ('payslip_name', models.CharField(max_length=60, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_pro_rated', models.BooleanField(default=False)),
                ('includes_employer_contribution', models.BooleanField(default=False)),
                ('frequency', models.CharField(max_length=120)),
                ('payroll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='benefits', to='payroll.payrollorg')),
            ],
        ),
        migrations.CreateModel(
            name='PaySchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('createdAt', models.DateTimeField(auto_now_add=True)),
                ('updatedAt', models.DateTimeField(auto_now=True)),
                ('payroll_start_month', models.CharField(max_length=60)),
                ('sunday', models.BooleanField(default=False)),
                ('monday', models.BooleanField(default=False)),
                ('tuesday', models.BooleanField(default=False)),
                ('wednesday', models.BooleanField(default=False)),
                ('thursday', models.BooleanField(default=False)),
                ('friday', models.BooleanField(default=False)),
                ('saturday', models.BooleanField(default=False)),
                ('second_saturday', models.BooleanField(default=False)),
                ('fourth_saturday', models.BooleanField(default=False)),
                ('payroll', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='payroll_scheduling', to='payroll.payrollorg')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Reimbursement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reimbursement_type', models.CharField(max_length=150)),
                ('payslip_name', models.CharField(max_length=60, unique=True)),
                ('include_in_flexible_benefit_plan', models.BooleanField()),
                ('unclaimed_reimbursement', models.BooleanField()),
                ('amount_value', models.IntegerField()),
                ('is_active', models.BooleanField(default=True)),
                ('payroll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reimbursements', to='payroll.payrollorg')),
            ],
        ),
        migrations.CreateModel(
            name='SalaryTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template_name', models.CharField(max_length=150)),
                ('description', models.CharField(blank=True, max_length=250, null=True)),
                ('annual_ctc', models.IntegerField()),
                ('earnings', models.JSONField(blank=True, default=list)),
                ('gross_salary', models.JSONField(blank=True, default=dict)),
                ('benefits', models.JSONField(blank=True, default=list)),
                ('total_ctc', models.JSONField(blank=True, default=dict)),
                ('deductions', models.JSONField(blank=True, default=list)),
                ('net_salary', models.JSONField(blank=True, default=dict)),
                ('payroll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='salary_templates', to='payroll.payrollorg')),
            ],
        ),
        migrations.CreateModel(
            name='WorkLocations',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('location_name', models.CharField(max_length=120)),
                ('address_line1', models.CharField(blank=True, max_length=150, null=True)),
                ('address_line2', models.CharField(blank=True, max_length=150, null=True)),
                ('address_state', models.CharField(blank=True, max_length=150, null=True)),
                ('address_city', models.CharField(blank=True, max_length=150, null=True)),
                ('address_pincode', models.PositiveIntegerField(null=True, validators=[payroll.models.validate_pincode])),
                ('payroll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='work_locations', to='payroll.payrollorg')),
            ],
        ),
        migrations.CreateModel(
            name='PT',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pt_number', models.CharField(blank=True, max_length=100, null=True)),
                ('slab', models.JSONField(blank=True, default=list)),
                ('deduction_cycle', models.CharField(default='Monthly', max_length=20)),
                ('payroll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pt_details', to='payroll.payrollorg')),
                ('work_location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pt_records', to='payroll.worklocations')),
            ],
        ),
        migrations.AddField(
            model_name='employeemanagement',
            name='work_location',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_work_location', to='payroll.worklocations'),
        ),
        migrations.AddConstraint(
            model_name='designation',
            constraint=models.UniqueConstraint(fields=('payroll', 'designation_name'), name='unique_designation_per_payroll'),
        ),
        migrations.AddConstraint(
            model_name='departments',
            constraint=models.UniqueConstraint(fields=('payroll', 'dept_code'), name='unique_dept_code_per_payroll'),
        ),
        migrations.AddConstraint(
            model_name='departments',
            constraint=models.UniqueConstraint(fields=('payroll', 'dept_name'), name='unique_dept_name_per_payroll'),
        ),
        migrations.AlterUniqueTogether(
            name='worklocations',
            unique_together={('payroll', 'location_name')},
        ),
        migrations.AlterUniqueTogether(
            name='pt',
            unique_together={('payroll', 'work_location')},
        ),
    ]
