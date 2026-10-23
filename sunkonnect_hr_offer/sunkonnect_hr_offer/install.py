import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
    create_custom_fields({
        "Job Offer": [
            {"fieldname":"custom_offer_salary_section","label":"Candidate Salary Breakup","fieldtype":"Section Break","insert_after":"offer_date","collapsible":1},
            {"fieldname":"custom_target_net_salary","label":"Target Monthly Take-home (before TDS)","fieldtype":"Currency","insert_after":"custom_offer_salary_section","reqd":0},
            {"fieldname":"custom_designation_level","label":"Designation Level","fieldtype":"Data","insert_after":"custom_target_net_salary","read_only":1},
            {"fieldname":"custom_wage_category","label":"Wage Category","fieldtype":"Select","options":"Unskilled\nSemi-skilled\nSkilled\nHighly skilled\nCustom","insert_after":"custom_designation_level","read_only":1},
            {"fieldname":"custom_wage_floor","label":"Applicable Monthly Wage Floor","fieldtype":"Currency","insert_after":"custom_wage_category","read_only":1},
            {"fieldname":"custom_basic_monthly","label":"Basic Pay (Monthly)","fieldtype":"Currency","insert_after":"custom_wage_floor","read_only":1},
            {"fieldname":"custom_hra_monthly","label":"HRA (Monthly)","fieldtype":"Currency","insert_after":"custom_basic_monthly","read_only":1},
            {"fieldname":"custom_special_allowance_monthly","label":"Special Allowance (Monthly)","fieldtype":"Currency","insert_after":"custom_hra_monthly","read_only":1},
            {"fieldname":"custom_gross_monthly","label":"Gross Earnings (Monthly)","fieldtype":"Currency","insert_after":"custom_special_allowance_monthly","read_only":1},
            {"fieldname":"custom_employee_pf_monthly","label":"Employee PF (Monthly)","fieldtype":"Currency","insert_after":"custom_gross_monthly","read_only":1},
            {"fieldname":"custom_employee_esi_monthly","label":"Employee ESI (Monthly)","fieldtype":"Currency","insert_after":"custom_employee_pf_monthly","read_only":1},
            {"fieldname":"custom_employee_lwf_monthly","label":"Employee LWF (Monthly)","fieldtype":"Currency","insert_after":"custom_employee_esi_monthly","read_only":1},
            {"fieldname":"custom_net_monthly","label":"Calculated Take-home Before TDS","fieldtype":"Currency","insert_after":"custom_employee_lwf_monthly","read_only":1},
            {"fieldname":"custom_employer_pf_monthly","label":"Employer PF/EDLI/Admin (Monthly)","fieldtype":"Currency","insert_after":"custom_net_monthly","read_only":1},
            {"fieldname":"custom_employer_esi_monthly","label":"Employer ESI (Monthly)","fieldtype":"Currency","insert_after":"custom_employer_pf_monthly","read_only":1},
            {"fieldname":"custom_employer_lwf_monthly","label":"Employer LWF (Monthly)","fieldtype":"Currency","insert_after":"custom_employer_esi_monthly","read_only":1},
            {"fieldname":"custom_gratuity_monthly","label":"Gratuity Accrual (Monthly)","fieldtype":"Currency","insert_after":"custom_employer_lwf_monthly","read_only":1},
            {"fieldname":"custom_statutory_bonus_monthly","label":"Statutory Bonus Costing (Monthly)","fieldtype":"Currency","insert_after":"custom_gratuity_monthly","read_only":1},
            {"fieldname":"custom_diwali_bonus_annual","label":"Diwali Bonus (Annual, if applicable)","fieldtype":"Currency","insert_after":"custom_statutory_bonus_monthly","read_only":1},
            {"fieldname":"custom_fixed_ctc_annual","label":"Fixed CTC (Annual)","fieldtype":"Currency","insert_after":"custom_diwali_bonus_annual","read_only":1},
            {"fieldname":"custom_variable_ctc_annual","label":"Indicative Variable Benefits (Annual)","fieldtype":"Currency","insert_after":"custom_fixed_ctc_annual","default":"0"},
            {"fieldname":"custom_total_ctc_annual","label":"Total Indicative CTC (Annual)","fieldtype":"Currency","insert_after":"custom_variable_ctc_annual","read_only":1},
            {"fieldname":"custom_salary_compliance_status","label":"Salary Compliance Checks","fieldtype":"Small Text","insert_after":"custom_total_ctc_annual","read_only":1},
            {"fieldname":"custom_salary_calculation_version","label":"Calculation Version","fieldtype":"Data","insert_after":"custom_salary_compliance_status","read_only":1,"hidden":1}
        ]
    }, update=True)
