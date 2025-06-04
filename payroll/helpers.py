import os
from decimal import Decimal, ROUND_HALF_UP


default_earnings = [
                    {
                        "component_name": "Basic",
                        "component_type": "Fixed",
                        "calculation_type": {
                            "type": "Percentage of CTC",
                            "value": 50
                        },
                        "is_active": True,
                        "is_part_of_employee_salary_structure": True,
                        "is_taxable": True,
                        "is_pro_rate_basis": True,
                        "includes_epf_contribution": True,
                        "includes_esi_contribution": True,
                        "is_included_in_payslip": True,
                        "tax_deduction_preference": None,
                        "is_scheduled_earning": True,
                        "pf_wage_less_than_15k": False,
                        "is_fbp_component": False,
                        "always_consider_epf_inclusion": True
                    },
                    {
                        "component_name": "HRA",
                        "component_type": "Fixed",
                        "calculation_type": {
                            "type": "Percentage of Basic",
                            "value": 50
                        },
                        "is_active": True,
                        "is_part_of_employee_salary_structure": True,
                        "is_taxable": True,
                        "is_pro_rate_basis": True,
                        "includes_epf_contribution": False,
                        "includes_esi_contribution": True,
                        "is_included_in_payslip": True,
                        "tax_deduction_preference": None,
                        "is_scheduled_earning": True,
                        "pf_wage_less_than_15k": False,
                        "is_fbp_component": False,
                        "always_consider_epf_inclusion": False

                    },
                    {
                        "component_name": "Fixed Allowance",
                        "component_type": "Fixed",
                        "calculation_type": {
                            "type": "Remaining balance pf CTC",
                            "value": 0
                        },
                        "is_active": True,
                        "is_part_of_employee_salary_structure": True,
                        "is_taxable": True,
                        "is_pro_rate_basis": True,
                        "includes_epf_contribution": True,
                        "includes_esi_contribution": True,
                        "is_included_in_payslip": True,
                        "tax_deduction_preference": None,
                        "is_scheduled_earning": True,
                        "pf_wage_less_than_15k": True,
                        "is_fbp_component": False,
                        "always_consider_epf_inclusion": False
                    },
                    {
                        "component_name": "Conveyance Allowance",
                        "component_type": "Fixed",
                        "calculation_type": {
                            "type": "Flat Amount",
                            "value": 0
                        },
                        "is_active": True,
                        "is_part_of_employee_salary_structure": True,
                        "is_taxable": True,
                        "is_pro_rate_basis": False,
                        "includes_epf_contribution": True,
                        "includes_esi_contribution": False,
                        "is_included_in_payslip": True,
                        "tax_deduction_preference": None,
                        "is_scheduled_earning": True,
                        "pf_wage_less_than_15k": True,
                        "is_fbp_component": False,
                        "always_consider_epf_inclusion": False
                    },
                    {
                        "component_name": "Bonus",
                        "component_type": "Fixed",
                        "calculation_type": {
                            "type": "Flat Amount",
                            "value": 0
                        },
                        "is_active": True,
                        "is_part_of_employee_salary_structure": True,
                        "is_taxable": True,
                        "is_pro_rate_basis": False,
                        "includes_epf_contribution": False,
                        "includes_esi_contribution": False,
                        "is_included_in_payslip": True,
                        "tax_deduction_preference": "TDS",
                        "is_scheduled_earning": True,
                        "pf_wage_less_than_15k": False,
                        "is_fbp_component": False,
                        "always_consider_epf_inclusion": False,
                    },
                    {
                        "component_name": "Commission",
                        "component_type": "Fixed",
                        "calculation_type": {
                            "type": "Flat Amount",
                            "value": 0
                        },
                        "is_active": True,
                        "is_part_of_employee_salary_structure": False,
                        "is_taxable": True,
                        "is_pro_rate_basis": False,
                        "includes_epf_contribution": False,
                        "includes_esi_contribution": True,
                        "is_included_in_payslip": True,
                        "tax_deduction_preference": None,
                        "is_scheduled_earning": False,
                        "pf_wage_less_than_15k": False,
                        "is_fbp_component": False,
                        "always_consider_epf_inclusion":False
                    },
                    {
                        "component_name": "Children Education Allowance",
                        "component_type": "Fixed",
                        "calculation_type": {
                            "type": "Flat Amount",
                            "value": 0
                        },
                        "is_active": True,
                        "is_part_of_employee_salary_structure": True,
                        "is_taxable": True,
                        "is_pro_rate_basis": True,
                        "includes_epf_contribution": True,
                        "includes_esi_contribution": True,
                        "is_included_in_payslip": True,
                        "tax_deduction_preference": None,
                        "is_scheduled_earning": True,
                        "pf_wage_less_than_15k": True,
                        "is_fbp_component": False,
                        "always_consider_epf_inclusion": False
                    },
                    {
                        "component_name": "Transport Allowance",
                        "component_type": "Fixed",
                        "calculation_type": {
                            "type": "Flat Amount",
                            "value": 0
                        },
                        "is_active": True,
                        "is_part_of_employee_salary_structure": True,
                        "is_taxable": True,
                        "is_pro_rate_basis": True,
                        "includes_epf_contribution": True,
                        "includes_esi_contribution": True,
                        "is_included_in_payslip": True,
                        "tax_deduction_preference": None,
                        "is_scheduled_earning": True,
                        "pf_wage_less_than_15k": True,
                        "is_fbp_component": False,
                        "always_consider_epf_inclusion": False
                    },
                    {
                        "component_name": "Travelling Allowance",
                        "component_type": "Fixed",
                        "calculation_type": {
                            "type": "Flat Amount",
                            "value": 0
                        },
                        "is_active": True,
                        "is_part_of_employee_salary_structure": True,
                        "is_taxable": True,
                        "is_pro_rate_basis": True,
                        "includes_epf_contribution": True,
                        "includes_esi_contribution": True,
                        "is_included_in_payslip": True,
                        "tax_deduction_preference": None,
                        "is_scheduled_earning": True,
                        "pf_wage_less_than_15k": True,
                        "is_fbp_component": False,
                        "always_consider_epf_inclusion": False,
                    },
                    {
                        "component_name": "Overtime Allowance",
                        "component_type": "Fixed",
                        "calculation_type": {
                            "type": "Flat Amount",
                            "value": 0
                        },
                        "is_active": True,
                        "is_part_of_employee_salary_structure": False,
                        "is_taxable": True,
                        "is_pro_rate_basis": False,
                        "includes_epf_contribution": False,
                        "includes_esi_contribution": True,
                        "is_included_in_payslip": True,
                        "tax_deduction_preference": None,
                        "is_scheduled_earning": False,
                        "pf_wage_less_than_15k": False,
                        "is_fbp_component": False,
                        "always_consider_epf_inclusion": False
                    }

]


default_leave_management = [
    {
        "name_of_leave": "Earned Leaves",
        "code": None,
        "leave_type": "Paid",
        "employee_leave_period": "Monthly",
        "number_of_leaves": 1.25,
        "pro_rate_leave_balance_of_new_joinees_based_on_doj": True,
        "reset_leave_balance": True,
        "reset_leave_balance_type": "Monthly",
        "carry_forward_unused_leaves": True,
        "max_carry_forward_days": 2,
        "encash_remaining_leaves": True,
        "encashment_days": 2
    },
    {
        "name_of_leave": "Casual Leaves",
        "code": None,
        "leave_type": "Paid",
        "employee_leave_period": "Monthly",
        "number_of_leaves": 1,
        "pro_rate_leave_balance_of_new_joinees_based_on_doj": True,
        "reset_leave_balance": True,
        "reset_leave_balance_type": "Monthly",
        "carry_forward_unused_leaves": True,
        "max_carry_forward_days": 2,
        "encash_remaining_leaves": True,
        "encashment_days": 2
    },
    {
        "name_of_leave": "Sick Leaves",
        "code": None,
        "leave_type": "Paid",
        "employee_leave_period": "Monthly",
        "number_of_leaves": 1,
        "pro_rate_leave_balance_of_new_joinees_based_on_doj": True,
        "reset_leave_balance": True,
        "reset_leave_balance_type": "Monthly",
        "carry_forward_unused_leaves": True,
        "max_carry_forward_days": 2,
        "encash_remaining_leaves": True,
        "encashment_days": 2
    },
    {
        "name_of_leave": "Loss of Pay",
        "code": None,
        "leave_type": "Unpaid",
        "employee_leave_period": "-",
        "number_of_leaves": 0,
        "pro_rate_leave_balance_of_new_joinees_based_on_doj": False,
        "reset_leave_balance": False,
        "reset_leave_balance_type": None,
        "carry_forward_unused_leaves": False,
        "max_carry_forward_days": 0,
        "encash_remaining_leaves": False,
        "encashment_days": 0
    },
]


def to_decimal_2places(value):
    try:
        decimal_value = Decimal(str(value))
        return decimal_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except Exception as e:
        print(f"Error converting to decimal: {e}")
        return Decimal('0.00')

def calculate_tds(regime_type, annual_salary, current_month, epf_value, ept_value):
    # Standard deductions
    standard_deduction_new = 75000
    standard_deduction_old = 50000

    # Rebate limits and max rebate values
    rebate_limit_new = 1200000       # Correct new tax regime rebate limit under 87A
    rebate_limit_old = 500000
    
    max_rebate_new = 60000          # For income up to ₹7,00,000 under new regime
    max_rebate_old = 12500

    cess_rate = 0.04

    month_left = 13 - current_month
    monthly_salary = annual_salary / 12
    salary_remaining = monthly_salary * month_left

    epf_value = epf_value * month_left
    ept_value = ept_value * month_left

    # Apply standard deduction based on the regime
    if regime_type == "new":
        prorated_deduction = standard_deduction_new + epf_value + ept_value
    else:
        prorated_deduction = standard_deduction_old + epf_value + ept_value

    # Calculate taxable income
    taxable_income = salary_remaining - prorated_deduction
    taxable_income = max(0, taxable_income)

    # Tax calculation for new regime
    def slab_tax_new(income):
        tax = 0
        slabs = [
            (400000, 0.0),
            (800000, 0.05),
            (1200000, 0.10),
            (1600000, 0.15),
            (2000000, 0.20),
            (2400000, 0.25),
            (float('inf'), 0.30)
        ]
        prev_limit = 0
        for limit, rate in slabs:
            if income > prev_limit:
                taxable = min(income, limit) - prev_limit
                tax += taxable * rate
                prev_limit = limit
            else:
                break
        return tax

    # Tax calculation for old regime
    def slab_tax_old(income):
        tax = 0
        slabs = [
            (250000, 0.0),
            (500000, 0.05),
            (1000000, 0.20),
            (float('inf'), 0.30)
        ]
        prev_limit = 0
        for limit, rate in slabs:
            if income > prev_limit:
                taxable = min(income, limit) - prev_limit
                tax += taxable * rate
                prev_limit = limit
            else:
                break
        return tax

    # Determine tax and rebate
    if regime_type == "new":
        tax_before_rebate = slab_tax_new(taxable_income)
        rebate = max_rebate_new if taxable_income <= rebate_limit_new else 0
    else:
        tax_before_rebate = slab_tax_old(taxable_income)
        rebate = max_rebate_old  if taxable_income <= rebate_limit_old else 0

    # Final tax calculation
    rebate = min(rebate, tax_before_rebate)
    tax_after_rebate = tax_before_rebate - rebate
    cess = tax_after_rebate * cess_rate
    total_tax = tax_after_rebate + cess

    monthly_tds = total_tax / month_left if month_left > 0 else 0

    return monthly_tds, taxable_income



def logo_upload_path(instance, filename):
    # Get the name of the business, replace spaces with underscores
    business_name = instance.business.nameOfBusiness.replace(' ', '_')
    # Construct the upload path
    return os.path.join(business_name, 'business_logos', filename)
