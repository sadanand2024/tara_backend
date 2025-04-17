from rest_framework import serializers
from .models import (PayrollOrg, WorkLocations, Departments, SalaryTemplate, PaySchedule,
                     Designation, EPF, ESI, PT, Earnings, Benefits, Deduction, Reimbursement,
                     HolidayManagement, LeaveManagement)
from .models import *
from datetime import date, datetime
from calendar import monthrange


class PayrollOrgSerializer(serializers.ModelSerializer):

    class Meta:
        model = PayrollOrg
        fields = '__all__'  # Include all fields from PayrollOrg model

    def create(self, validated_data):
        """
        Create and return a new `PayrollOrg` instance, given the validated data.
        """
        # Create a new PayrollOrg instance using the validated data
        instance = self.Meta.model(**validated_data)
        instance.save()  # Save the instance to the database
        return instance

    def update(self, instance, validated_data):
        """
        Update and return an existing `PayrollOrg` instance, given the validated data.
        """
        # Update the instance attributes with the validated data
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()  # Save the updated instance to the database
        return instance




class WorkLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkLocations
        fields = '__all__'

    def create(self, validated_data):
        """
        Create and return a new `WorkLocations` instance, given the validated data.
        """
        instance = WorkLocations(**validated_data)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        """
        Update and return an existing `WorkLocations` instance, given the validated data.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class DepartmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departments
        fields = '__all__'

    def create(self, validated_data):
        """
        Create and return a new `Department` instance, given the validated data.
        """
        instance = self.Meta.model(**validated_data)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        """
        Update and return an existing `Department` instance, given the validated data.
        """
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation
        fields = ['id', 'payroll', 'designation_name']

    def create(self, validated_data):
        """
        Create and return a new `WorkLocations` instance, given the validated data.
        """
        instance = Designation(**validated_data)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        """
        Update and return an existing `WorkLocations` instance, given the validated data.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class EPFSerializer(serializers.ModelSerializer):
    class Meta:
        model = EPF
        fields = ['id', 'payroll', 'epf_number', 'employee_contribution_rate', 'employer_contribution_rate',
                  'employer_edil_contribution_in_ctc', 'include_employer_contribution_in_ctc',
                  'admin_charge_in_ctc', 'allow_employee_level_override', 'prorate_restricted_pf_wage',
                  'apply_components_if_wage_below_15k', 'is_disabled']

    def create(self, validated_data):
        """
        Create and return a new `WorkLocations` instance, given the validated data.
        """
        instance = EPF(**validated_data)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        """
        Update and return an existing `WorkLocations` instance, given the validated data.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ESISerializer(serializers.ModelSerializer):
    class Meta:
        model = ESI
        fields = ['id', 'payroll', 'esi_number', 'employee_contribution', 'employer_contribution',
                  'include_employer_contribution_in_ctc', 'is_disabled']

    def create(self, validated_data):
        """
        Create and return a new `WorkLocations` instance, given the validated data.
        """
        instance = ESI(**validated_data)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        """
        Update and return an existing `WorkLocations` instance, given the validated data.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class PTSerializer(serializers.ModelSerializer):
    slab = serializers.JSONField(default=list)

    class Meta:
        model = PT
        fields = ['id', 'payroll', 'work_location', 'pt_number', 'slab', 'deduction_cycle']

    def create(self, validated_data):
        """
        Create and return a new `PF` instance, given the validated data.
        """
        instance = PT.objects.create(**validated_data)
        return instance

    def update(self, instance, validated_data):
        """
        Update and return an existing `PF` instance, given the validated data.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class PTSerializerRetrieval(serializers.ModelSerializer):
    work_location_name = serializers.CharField(source='work_location.location_name', read_only=True)
    state = serializers.CharField(source='work_location.address_state', read_only=True)
    slab = serializers.ListField(
        child=serializers.DictField(),  # Each element inside the list is a dictionary (object)
        allow_empty=True  # Allow the list to be empty, if necessary
    )

    class Meta:
        model = PT
        fields = ['id', 'payroll', 'work_location', 'work_location_name', 'state', 'pt_number', 'slab']


class EarningsSerializer(serializers.ModelSerializer):
    calculation_type = serializers.JSONField(default=dict)

    class Meta:
        model = Earnings
        fields = [
            'id', 'payroll', 'component_name', 'component_type', 'is_active', 'calculation_type',
            'is_part_of_employee_salary_structure', 'is_taxable', 'is_pro_rate_basis',
            'is_fbp_component', 'includes_epf_contribution', 'includes_esi_contribution',
            'is_included_in_payslip', 'tax_deduction_preference', 'is_scheduled_earning', 'pf_wage_less_than_15k',
            'always_consider_epf_inclusion'

        ]

    def create(self, validated_data):
        """
        Create and return a new `Earnings` instance, given the validated data.
        """
        instance = Earnings.objects.create(**validated_data)
        return instance

    def update(self, instance, validated_data):
        """
        Update and return an existing `Earnings` instance, given the validated data.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class EarningsSerializerRetrieval(serializers.ModelSerializer):
    calculation = serializers.SerializerMethodField()
    consider_for_epf = serializers.SerializerMethodField()
    consider_for_esi = serializers.SerializerMethodField()

    class Meta:
        model = Earnings
        fields = [
            'id', 'component_name', 'calculation', 'consider_for_epf',
            'consider_for_esi', 'is_active'
        ]

    def get_calculation(self, obj):
        """Format the calculation field based on calculation_type"""
        calc_type = obj.calculation_type.get("type", "")
        value = obj.calculation_type.get("value", "")

        if calc_type == "Percentage of CTC":
            return f"{value}% of CTC"
        elif calc_type == "Percentage of Basic":
            return f"{value}% of Basic"
        elif calc_type == "Flat Amount":
            return "Flat Amount"
        elif value and calc_type:
            return f"{value} ({calc_type})"
        elif calc_type:
            return calc_type
        else:
            return "Unknown"

    def get_consider_for_epf(self, obj):
        """Return 'True' if EPF is included, otherwise conditionally 'True(pf wage < 16k)'"""
        if obj.includes_epf_contribution:
            return "Yes(pf wage < 15k)" if obj.pf_wage_less_than_15k else "Yes"
        return "No"

    def get_consider_for_esi(self, obj):
        """Return 'Yes' if includes_esi_contribution is True, otherwise 'No'"""
        return "Yes" if obj.includes_esi_contribution else "No"


class BenefitsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benefits
        fields = [
            'id',
            'payroll',
            'benefit_type',
            'associated_with',
            'payslip_name',
            'is_active',
            'is_pro_rated',
            'includes_employer_contribution',
            'frequency'
        ]

    # Adding validation for unique `payslip_name`
    def validate_payslip_name(self, value):
        if Benefits.objects.filter(payslip_name=value).exists():
            raise serializers.ValidationError("Payslip name must be unique.")
        return value


class DeductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deduction
        fields = [
            'id',
            'payroll',
            'deduction_type',
            'payslip_name',
            'is_active',
            'frequency'
        ]

    def validate_payslip_name(self, value):
        if Deduction.objects.filter(payslip_name=value).exists():
            raise serializers.ValidationError("Payslip name must be unique.")
        return value


class ReimbursementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reimbursement
        fields = [
            'id',
            'payroll',
            'reimbursement_type',
            'payslip_name',
            'include_in_flexible_benefit_plan',
            'unclaimed_reimbursement',
            'amount_value',
            'is_active'
        ]

    def validate_payslip_name(self, value):
        if Reimbursement.objects.filter(payslip_name=value).exists():
            raise serializers.ValidationError("Payslip name must be unique.")
        return value

    def validate_amount_value(self, value):
        if value <= 0:
            raise serializers.ValidationError("Reimbursement amount must be greater than zero.")
        return value


class SalaryTemplateSerializer(serializers.ModelSerializer):
    earnings = serializers.JSONField(default=list)
    gross_salary = serializers.JSONField(default=list)
    benefits = serializers.JSONField(default=list)
    total_ctc = serializers.JSONField(default=list)
    deductions = serializers.JSONField(default=list)
    net_salary = serializers.JSONField(default=list)

    class Meta:
        model = SalaryTemplate
        fields = '__all__'

    def create(self, validated_data):
        """
        Create and return a new `Earnings` instance, given the validated data.
        """
        instance = SalaryTemplate.objects.create(**validated_data)
        return instance

    def update(self, instance, validated_data):
        """
        Update and return an existing `Earnings` instance, given the validated data.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class PayScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaySchedule
        fields = '__all__'

    def validate(self, data):
        """ Custom validation to ensure at least two days are selected """
        selected_days = sum([
            data.get('sunday', False), data.get('monday', False), data.get('tuesday', False),
            data.get('wednesday', False), data.get('thursday', False), data.get('friday', False),
            data.get('saturday', False), data.get('second_saturday', False), data.get('fourth_saturday', False)
        ])
        if selected_days < 2:
            raise serializers.ValidationError("At least two days must be selected.")
        return data

    def create(self, validated_data):
        """
        Create and return a new `Earnings` instance, given the validated data.
        """
        instance = PaySchedule.objects.create(**validated_data)
        return instance

    def update(self, instance, validated_data):
        """Ensure that update returns the instance"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class LeaveManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveManagement
        fields = '__all__'

    def create(self, validated_data):
        """
        Create and return a new `Earnings` instance, given the validated data.
        """
        instance = LeaveManagement.objects.create(**validated_data)
        return instance

    def update(self, instance, validated_data):
        """
        Update and return an existing `Earnings` instance, given the validated data.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class HolidayManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = HolidayManagement
        fields = '__all__'
        
    def create(self, validated_data):
        """
        Create and return a new `Earnings` instance, given the validated data.
        """
        instance = HolidayManagement.objects.create(**validated_data)
        return instance

    def update(self, instance, validated_data):
        """
        Update and return an existing `Earnings` instance, given the validated data.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class EmployeeManagementSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmployeeManagement
        fields = '__all__'


class EmployeeSalaryDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeSalaryDetails
        fields = '__all__'


class SimplifiedEmployeeSalarySerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()
    previous_ctc = serializers.SerializerMethodField()
    current_ctc = serializers.DecimalField(source='annual_ctc', max_digits=12, decimal_places=2)
    employee_id = serializers.IntegerField(source='employee.id')
    associate_id = serializers.CharField(source='employee.associate_id')  # Added based on your model

    class Meta:
        model = EmployeeSalaryDetails
        fields = [
            'id',
            'employee_id',
            'associate_id',  # Include associate_id in response
            'employee_name',
            'department',
            'designation',
            'previous_ctc',
            'current_ctc',
            'created_on'
        ]

    def get_employee_name(self, obj):
        # Handle potential None values for middle name
        middle_name = f" {obj.employee.middle_name}" if obj.employee.middle_name else ""
        return f"{obj.employee.first_name}{middle_name} {obj.employee.last_name}"

    def get_department(self, obj):
        return obj.employee.department.dept_name if obj.employee.department else None

    def get_designation(self, obj):
        return obj.employee.designation.designation_name if obj.employee.designation else None

    def get_previous_ctc(self, obj):
        previous_salary = (
            EmployeeSalaryDetails.objects
            .filter(employee=obj.employee, id__lt=obj.id)
            .order_by('-id')
            .first()
        )
        return previous_salary.annual_ctc if previous_salary else None


class EmployeePersonalDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeePersonalDetails
        fields = '__all__'


class EmployeeBankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeBankDetails
        fields = '__all__'


class EmployeeDataSerializer(serializers.ModelSerializer):
    employee_salary = EmployeeSalaryDetailsSerializer(many=True, read_only=True)
    employee_personal_details = EmployeePersonalDetailsSerializer(read_only=True)
    employee_bank_details = EmployeeBankDetailsSerializer(read_only=True)

    designation_name = serializers.CharField(source='designation.designation_name', read_only=True)
    department_name = serializers.CharField(source='department.dept_name', read_only=True)

    class Meta:
        model = EmployeeManagement
        fields = '__all__'


class CurrentMonthEmployeeDataSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    total_days_in_month = serializers.SerializerMethodField()
    paid_days = serializers.SerializerMethodField()
    gross_salary = serializers.SerializerMethodField()
    annual_ctc = serializers.SerializerMethodField()

    designation_name = serializers.CharField(source='designation.designation_name', read_only=True)
    department_name = serializers.CharField(source='department.dept_name', read_only=True)

    class Meta:
        model = EmployeeManagement
        fields = [
            "id",
            "employee_name",
            "department_name",
            "designation_name",
            "doj",
            "total_days_in_month",
            "paid_days",
            "gross_salary",
            "annual_ctc",
        ]

    def get_employee_name(self, obj):
        return f"{obj.first_name} {obj.middle_name} {obj.last_name}".strip()

    def get_total_days_in_month(self, obj):
        """Returns the total days in the month of DOJ (Joining Date)."""
        doj_date = obj.doj
        _, days_in_month = monthrange(doj_date.year, doj_date.month)
        return days_in_month

    def get_paid_days(self, obj):
        """Calculates paid days = Total Days - Holidays - Off Days from PaySchedule"""
        doj_date = obj.doj
        year, month = doj_date.year, doj_date.month
        _, days_in_month = monthrange(year, month)

        # 🔹 Step 1: Get PaySchedule for the Payroll
        pay_schedule = PaySchedule.objects.filter(payroll=obj.payroll).first()

        # Get first and last day of the month
        first_day = datetime(year, month, 1).date()
        last_day = datetime(year, month, days_in_month).date()

        # Fetch all holidays in that month
        holidays = HolidayManagement.objects.filter(
            payroll=obj.payroll,
            start_date__gte=first_day,
            start_date__lte=last_day
        ).values_list('start_date', flat=True)

        # 🔹 Step 3: Determine Off Days (Saturdays, Sundays, etc.)
        off_days = set()
        for day in range(1, days_in_month + 1):
            date = doj_date.replace(day=day)
            weekday = date.weekday()  # 0 = Monday, 6 = Sunday

            if pay_schedule:
                if (weekday == 0 and pay_schedule.monday) or \
                   (weekday == 1 and pay_schedule.tuesday) or \
                   (weekday == 2 and pay_schedule.wednesday) or \
                   (weekday == 3 and pay_schedule.thursday) or \
                   (weekday == 4 and pay_schedule.friday) or \
                   (weekday == 5 and pay_schedule.saturday) or \
                   (weekday == 6 and pay_schedule.sunday):
                    off_days.add(date)

                # Handle Second & Fourth Saturday
                if pay_schedule.second_saturday and (day >= 8 and day <= 14 and weekday == 5):
                    off_days.add(date)
                if pay_schedule.fourth_saturday and (day >= 22 and day <= 28 and weekday == 5):
                    off_days.add(date)

        # 🔹 Step 4: Calculate Paid Days
        paid_days = days_in_month - len(holidays) - len(off_days)

        return max(0, paid_days)  # Ensure it doesn't go negative

    def get_gross_salary(self, obj):
        """Retrieves the latest gross salary (monthly) of the employee."""
        latest_salary = obj.employee_salary.filter(valid_to__isnull=True).first()  # Get active salary
        return latest_salary.gross_salary.get('monthly', 0) if latest_salary and latest_salary.gross_salary else 0

    def get_annual_ctc(self, obj):
        """Retrieves the latest annual CTC of the employee."""
        latest_salary = obj.employee_salary.filter(valid_to__isnull=True).first()  # Get active salary
        return latest_salary.annual_ctc if latest_salary else 0


class PayrollEPFESISerializer(serializers.ModelSerializer):
    epf_details = EPFSerializer(read_only=True)
    esi_details = ESISerializer(read_only=True)
    pt_details = PTSerializer(many=True, read_only=True)

    class Meta:
        model = PayrollOrg
        fields = ['id', 'epf_details', 'esi_details', 'pt_details']


class EmployeeExitSerializer(serializers.ModelSerializer):
    department = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeExit
        fields = '__all__'

    def get_department(self, obj):
        """Fetch employee's department"""
        return obj.employee.department.dept_name

    def get_designation(self, obj):
        """Fetch employee's designation"""
        return obj.employee.designation.designation_name


class AdvanceLoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdvanceLoan
        fields = '__all__'

    def validate(self, data):
        """Ensure no_of_months is valid"""
        if data.get('no_of_months') <= 0:
            raise serializers.ValidationError({"error": "Number of months must be greater than zero."})
        return data


class BonusIncentiveSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()

    class Meta:
        model = BonusIncentive
        fields = '__all__'

    def get_employee_name(self, obj):
        """Returns the formatted employee name"""
        return f"{obj.employee.first_name} {obj.employee.middle_name} {obj.employee.last_name}".strip()

    def get_department(self, obj):
        """Fetch employee's department"""
        return obj.employee.department.dept_name

    def get_designation(self, obj):
        """Fetch employee's designation"""
        return obj.employee.designation.designation_name


class AdvanceLoanDetailSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()

    class Meta:
        model = AdvanceLoan
        fields = '__all__'

    def get_employee_name(self, obj):
        """Returns the formatted employee name"""
        return f"{obj.employee.first_name} {obj.employee.middle_name} {obj.employee.last_name}".strip()

    def get_department(self, obj):
        """Fetch employee's department"""
        return obj.employee.department.dept_name

    def get_designation(self, obj):
        """Fetch employee's designation"""
        return obj.employee.designation.designation_name

class AdvanceLoanSummarySerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()
    pending_balance = serializers.SerializerMethodField()
    current_month_deduction = serializers.SerializerMethodField()

    class Meta:
        model = AdvanceLoan
        fields = [
            "id",
            "employee_name",
            "department",
            "designation",
            "loan_type",
            "amount",
            "emi_amount",
            "end_month",
            "pending_balance",
            "current_month_deduction"
        ]

    def get_employee_name(self, obj):
        """Returns the formatted employee name"""
        return f"{obj.employee.first_name} {obj.employee.middle_name} {obj.employee.last_name}".strip()

    def get_department(self, obj):
        """Fetch employee's department"""
        return obj.employee.department.dept_name

    def get_designation(self, obj):
        """Fetch employee's designation"""
        return obj.employee.designation.designation_name

    def get_pending_balance(self, obj):
        """Calculates remaining loan balance"""
        current_date = self.context.get("current_date")
        if not current_date:
            current_date = datetime.now().date()

        months_paid = (current_date.year - obj.start_month.year) * 12 + (current_date.month - obj.start_month.month)
        pending_balance = obj.amount - (months_paid * obj.emi_amount)

        return max(0, pending_balance)  # Ensure no negative balance

    def get_current_month_deduction(self, obj):
        """Returns EMI deduction for the current month"""
        pending_balance = self.get_pending_balance(obj)
        return obj.emi_amount if pending_balance > 0 else 0


class EmployeeAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeAttendance
        fields = '__all__'


class EmployeeSalaryHistorySerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeSalaryHistory
        fields = '__all__'

    def get_employee_name(self, obj):
        """Returns the formatted employee name"""
        return f"{obj.employee.first_name} {obj.employee.middle_name} {obj.employee.last_name}".strip()

    def get_department(self, obj):
        """Fetch employee's department"""
        return obj.employee.department.dept_name

    def get_designation(self, obj):
        """Fetch employee's designation"""
        return obj.employee.designation.designation_name