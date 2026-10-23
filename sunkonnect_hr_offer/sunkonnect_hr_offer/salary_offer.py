"""Candidate-facing offer calculator. Rates are copied from Recruitment.xlsx and must be validated by HR/CA before production use."""
import frappe
import math
from frappe.utils import flt

VERSION = "xlsx-map-0.1"
DEFAULTS = {
    "basic_pct": 0.60, "hra_pct_of_basic": 0.40,
    "pf_ceiling": 25000, "restrict_pf_to_ceiling": 1,
    "employee_pf_pct": 0.12, "employer_pf_pct": 0.12,
    "eps_pct": 0.0833, "edli_pct": 0.005, "pf_admin_pct": 0.005,
    "esi_threshold": 21000, "employee_esi_pct": 0.0075,
    "employer_esi_pct": 0.0325, "bonus_ceiling": 21000,
    "bonus_floor": 7000, "bonus_min_pct": 0.0833,
    "diwali_bonus_annual": 5100, "diwali_treatment": "Statutory",
    "employee_lwf_monthly": 35, "employer_lwf_monthly": 70,
    "gratuity_pct": 0.0481, "max_exclusions_pct": 0.50,
    "minimum_wages": {"Unskilled": 15220.71, "Semi-skilled": 16780.74, "Skilled": 18500.81, "Highly skilled": 19425.85},
}


def get_policy():
    """Read configurable policy; use workbook-mapped defaults if settings are not yet created."""
    if not frappe.db.exists("DocType", "Salary Offer Policy"):
        return DEFAULTS
    p = frappe.get_single("Salary Offer Policy")
    d = dict(DEFAULTS)
    for k in DEFAULTS:
        if hasattr(p, k):
            val = getattr(p, k)
            if val is not None and val != "": d[k] = val
    # child wage table is managed by HR; values take precedence over defaults
    if getattr(p, "wage_rates", None):
        d["minimum_wages"] = {r.wage_category: flt(r.monthly_rate) for r in p.wage_rates if r.wage_category and flt(r.monthly_rate) >= 0}
    return d


def get_designation_mapping(designation):
    if frappe.db.exists("DocType", "Salary Offer Policy"):
        p = frappe.get_single("Salary Offer Policy")
        for r in getattr(p, "designation_mappings", []) or []:
            if (r.designation or "").strip().casefold() == (designation or "").strip().casefold():
                return {"level": r.level or "", "category": r.wage_category or "Skilled", "trainee": bool(r.trainee)}
    # Workbook role table, exact designation mapping
    rows = {
        "CXO": ("L1", "Highly skilled", False), "Sr. VP": ("L2", "Highly skilled", False),
        "VP": ("L2", "Highly skilled", False), "AVP": ("L2", "Highly skilled", False),
        "General Manager": ("L3", "Highly skilled", False), "Sr. Manager": ("L3", "Highly skilled", False),
        "Manager": ("L3", "Highly skilled", False), "Asst. Manager": ("L3", "Highly skilled", False),
        "Sr. Consultant / Sr. Executive / Sr. Engineer": ("L4", "Highly skilled", False),
        "Consultant / Executive / Engineer": ("L4", "Skilled", False),
        "Consultant / Executive / Engineer – site lead / sign-off": ("L4", "Highly skilled", False),
        "Sr. Analyst": ("L5", "Skilled", False),
        "Analyst – engineering / PV Tech / BoS / PMC": ("L5", "Skilled", False),
        "Analyst – administration / data entry / telecalling / coordination": ("L5", "Semi-skilled", False),
        "Intern – engineering (any qualification)": ("L6", "Skilled", True),
        "Intern – non-engineering (any qualification)": ("L6", "Semi-skilled", True),
        "Site Supervisor": ("—", "Highly skilled", False), "Site Technician / Electrician": ("—", "Skilled", False),
        "Driver (light vehicle)": ("—", "Skilled", False), "Accountant / HR Executive": ("—", "Skilled", False),
        "Receptionist / Office Coordinator": ("—", "Semi-skilled", False), "Site Helper / Office Boy / Housekeeping": ("—", "Unskilled", False),
    }
    return {"level": rows.get(designation, ("", "Skilled", False))[0], "category": rows.get(designation, ("", "Skilled", False))[1], "trainee": rows.get(designation, ("", "Skilled", False))[2]}


def calculate(target_net, designation, variable_ctc_annual=0, policy=None):
    """Solve the gross needed for a target net, then calculate workbook-mapped monthly/annual values."""
    p = dict(DEFAULTS); p.update(policy or {})
    # Frappe Percent fields return percentage points (e.g. 60); calculator uses decimals (0.60).
    for key in ("basic_pct", "hra_pct_of_basic", "employee_pf_pct", "employer_pf_pct", "edli_pct", "pf_admin_pct", "employee_esi_pct", "employer_esi_pct", "bonus_min_pct", "gratuity_pct", "max_exclusions_pct"):
        if flt(p.get(key)) > 1:
            p[key] = flt(p[key]) / 100.0
    mapping = get_designation_mapping(designation)
    category = mapping["category"]
    wages = p.get("minimum_wages", DEFAULTS["minimum_wages"])
    category_floor = flt(wages.get(category, wages.get("Unskilled", 0)))
    basic_pct = flt(p["basic_pct"])
    if basic_pct <= 0 or basic_pct > 1: frappe.throw("Basic % must be greater than 0 and at most 100%.")
    wage_floor = max(category_floor * 0.75, flt(wages.get("Unskilled", 0))) if mapping["trainee"] else category_floor
    pf_base = lambda basic: min(basic, flt(p["pf_ceiling"])) if p["restrict_pf_to_ceiling"] else basic
    def amounts(gross):
        basic = round(gross * basic_pct)
        hra = round(basic * flt(p["hra_pct_of_basic"]))
        emp_pf = round(flt(p["employee_pf_pct"]) * pf_base(basic))
        emp_esi = math.ceil(gross * flt(p["employee_esi_pct"])) if gross <= flt(p["esi_threshold"]) else 0
        emp_lwf = flt(p["employee_lwf_monthly"])
        net = gross - emp_pf - emp_esi - emp_lwf
        return basic, hra, gross-basic-hra, emp_pf, emp_esi, emp_lwf, net
    # Minimum gross satisfying both net target and statutory basic floor.
    low = max(0, wage_floor / basic_pct)
    high = max(low + 1, flt(target_net) * 3 + 10000)
    for _ in range(80):
        if amounts(high)[-1] >= flt(target_net): break
        high *= 2
    for _ in range(100):
        mid = (low + high) / 2
        if amounts(mid)[-1] >= flt(target_net): high = mid
        else: low = mid
    gross = round(high)
    # Re-check rounding and floor after integer rounding
    while amounts(gross)[-1] < flt(target_net) or round(gross*basic_pct) < wage_floor: gross += 1
    basic, hra, special, emp_pf, emp_esi, emp_lwf, net = amounts(gross)
    employer_pf = round(flt(p["employer_pf_pct"])*pf_base(basic)) + round(flt(p["edli_pct"])*min(basic, flt(p["pf_ceiling"]))) + round(flt(p["pf_admin_pct"])*pf_base(basic))
    employer_esi = math.ceil(gross*flt(p["employer_esi_pct"])) if gross <= flt(p["esi_threshold"]) else 0
    employer_lwf = flt(p["employer_lwf_monthly"])
    gratuity = round(basic*flt(p["gratuity_pct"]))
    bonus_eligible = basic <= flt(p["bonus_ceiling"])
    bonus_base = max(flt(p["bonus_floor"]), category_floor)
    statutory_bonus_annual = max(round(bonus_base*flt(p["bonus_min_pct"])*12), flt(p["diwali_bonus_annual"])) if bonus_eligible else 0
    statutory_bonus_monthly = round(statutory_bonus_annual/12) if bonus_eligible else 0
    diwali_annual = 0 if bonus_eligible else flt(p["diwali_bonus_annual"])
    fixed_ctc_monthly = gross + employer_pf + employer_esi + employer_lwf + gratuity + statutory_bonus_monthly + diwali_annual/12
    fixed_ctc_annual = round(gross*12 + employer_pf*12 + employer_esi*12 + employer_lwf*12 + gratuity*12 + statutory_bonus_annual + diwali_annual)
    variable_annual = flt(variable_ctc_annual)
    # Workbook's exclusions test is indicative and requires legal/CA sign-off.
    excluded = hra + special + emp_pf + (0 if p.get("diwali_treatment") == "Wages" else diwali_annual/12)
    remuneration = max(1, gross + employer_pf + (diwali_annual/12))
    exclusion_pct = excluded / remuneration
    checks = [
        "Basic wage floor: PASS" if basic >= wage_floor else "Basic wage floor: REVIEW",
        "Target take-home: PASS" if net >= flt(target_net) else "Target take-home: REVIEW",
        "ESI: applicable" if gross <= flt(p["esi_threshold"]) else "ESI: not applicable by configured threshold",
        "Statutory bonus: eligible" if bonus_eligible else "Statutory bonus: not eligible by configured ceiling",
        ("Code on Wages exclusions ratio: PASS (indicative)" if exclusion_pct <= flt(p["max_exclusions_pct"]) else "Code on Wages exclusions ratio: REVIEW (indicative)"),
        "Rates/ceilings and Haryana wage notification require HR/CA validation before issue."
    ]
    return {"designation_level":mapping["level"],"wage_category":category,"wage_floor":round(wage_floor,2),"basic_monthly":basic,"hra_monthly":hra,"special_allowance_monthly":special,"gross_monthly":gross,"employee_pf_monthly":emp_pf,"employee_esi_monthly":emp_esi,"employee_lwf_monthly":emp_lwf,"net_monthly":net,"employer_pf_monthly":employer_pf,"employer_esi_monthly":employer_esi,"employer_lwf_monthly":employer_lwf,"gratuity_monthly":gratuity,"statutory_bonus_monthly":statutory_bonus_monthly,"diwali_bonus_annual":diwali_annual,"fixed_ctc_annual":fixed_ctc_annual,"variable_ctc_annual":variable_annual,"total_ctc_annual":fixed_ctc_annual+variable_annual,"compliance_status":"\n".join(checks),"calculation_version":VERSION}


def validate_job_offer(doc, method=None):
    # Do not rewrite submitted/released offers: keep their salary as a snapshot.
    if doc.docstatus != 0 or not flt(doc.get("custom_target_net_salary")):
        return
    designation = doc.get("designation") or ""
    if not designation:
        return
    p = get_policy()
    result = calculate(doc.custom_target_net_salary, designation, doc.get("custom_variable_ctc_annual") or 0, p)
    for key, value in result.items():
        doc.set("custom_" + key, value)


def get_hiring_budget(designation):
    """Return configured designation-wise CTC budget, if maintained by HR."""
    if not designation or not frappe.db.exists("DocType", "Salary Offer Policy"):
        return {}
    policy = frappe.get_single("Salary Offer Policy")
    rows = [r for r in (getattr(policy, "hiring_budgets", None) or []) if r.designation == designation]
    if not rows:
        return {}
    # If multiple rows exist for the same role, display all ranges in the UI;
    # server-side calculation uses the first configured slab for status.
    row = rows[0]
    return {
        "budget_min_annual_ctc": flt(row.min_annual_ctc),
        "budget_max_annual_ctc": flt(row.max_annual_ctc),
        "budget_approved_positions": int(row.approved_positions or 0),
        "budget_financial_year": row.financial_year or "",
        "budget_note": row.budget_note or "",
        "budget_slabs": [{"min": flt(r.min_annual_ctc), "max": flt(r.max_annual_ctc), "positions": int(r.approved_positions or 0), "financial_year": r.financial_year or "", "note": r.budget_note or ""} for r in rows],
    }


@frappe.whitelist()
def fetch_designation_budget(designation):
    if not frappe.has_permission("Salary Offer Calculator", "read"):
        frappe.throw("Not permitted to view salary offer budgets", frappe.PermissionError)
    return get_hiring_budget(designation)


@frappe.whitelist()
def calculate_pre_offer(docname=None, designation=None, target_net_salary=None, variable_ctc_annual=0):
    """Calculate a pre-offer CTC estimate and compare it with the role budget."""
    if not frappe.has_permission("Salary Offer Calculator", "read"):
        frappe.throw("Not permitted to calculate salary offers", frappe.PermissionError)
    if docname:
        doc = frappe.get_doc("Salary Offer Calculator", docname)
        designation = doc.designation
        target_net_salary = doc.target_net_salary
        variable_ctc_annual = doc.variable_ctc_annual or 0
    if not designation or flt(target_net_salary) <= 0:
        frappe.throw("Select a designation and enter the agreed monthly in-hand salary first.")
    result = calculate(target_net_salary, designation, variable_ctc_annual, get_policy())
    budget = get_hiring_budget(designation)
    total = flt(result.get("total_ctc_annual"))
    if not budget:
        budget_status = "BUDGET NOT CONFIGURED — add a slab in Salary Offer Policy"
    elif total < flt(budget.get("budget_min_annual_ctc")):
        budget_status = "BELOW DESIGNATION BUDGET RANGE — review grade and approved package"
    elif total > flt(budget.get("budget_max_annual_ctc")):
        budget_status = "OVER BUDGET — approval required before offer"
    else:
        budget_status = "WITHIN DESIGNATION BUDGET"
    result.update(budget)
    result["budget_status"] = budget_status
    result["target_net_salary"] = flt(target_net_salary)
    return result


def validate_pre_offer_calculator(doc, method=None):
    if not doc.designation or not flt(doc.target_net_salary):
        return
    result = calculate(doc.target_net_salary, doc.designation, doc.variable_ctc_annual or 0, get_policy())
    budget = get_hiring_budget(doc.designation)
    result.update(budget)
    total = flt(result.get("total_ctc_annual"))
    if not budget:
        result["budget_status"] = "BUDGET NOT CONFIGURED — add a slab in Salary Offer Policy"
    elif total < flt(budget.get("budget_min_annual_ctc")):
        result["budget_status"] = "BELOW DESIGNATION BUDGET RANGE — review grade and approved package"
    elif total > flt(budget.get("budget_max_annual_ctc")):
        result["budget_status"] = "OVER BUDGET — approval required before offer"
    else:
        result["budget_status"] = "WITHIN DESIGNATION BUDGET"
    result["target_net_salary"] = flt(doc.target_net_salary)
    for key, value in result.items():
        if key in doc.as_dict():
            doc.set(key, value)


@frappe.whitelist()
def create_job_offer_from_calculator(name):
    """Create a standard draft Job Offer only after negotiation is accepted.
    The target take-home is copied unchanged and recalculated using current policy.
    """
    calc_doc = frappe.get_doc("Salary Offer Calculator", name)
    calc_doc.check_permission("write")
    if calc_doc.job_offer:
        return {"job_offer": calc_doc.job_offer, "already_created": True}
    if calc_doc.negotiation_status != "Accepted":
        frappe.throw("Set Negotiation Status to Accepted before creating the Job Offer.")
    if not calc_doc.job_applicant:
        frappe.throw("Link a Job Applicant before creating the Job Offer.")
    if not calc_doc.company:
        frappe.throw("Select the company before creating the Job Offer.")
    if not flt(calc_doc.target_net_salary):
        frappe.throw("Agreed monthly in-hand salary is required.")
    validate_pre_offer_calculator(calc_doc)
    if (calc_doc.budget_status or "").startswith("OVER BUDGET"):
        frappe.throw("This CTC is above the designation hiring budget. Obtain approval/update the budget before creating the Job Offer.")
    offer = frappe.new_doc("Job Offer")
    offer.job_applicant = calc_doc.job_applicant
    if "applicant_name" in offer.as_dict():
        offer.applicant_name = calc_doc.applicant_name or frappe.db.get_value("Job Applicant", calc_doc.job_applicant, "applicant_name")
    offer.designation = calc_doc.designation
    offer.company = calc_doc.company
    offer.offer_date = frappe.utils.today()
    offer.custom_target_net_salary = calc_doc.target_net_salary  # preserve negotiated in-hand target exactly
    offer.custom_variable_ctc_annual = calc_doc.variable_ctc_annual or 0
    offer.insert()
    calc_doc.job_offer = offer.name
    calc_doc.conversion_note = "Created from pre-offer calculator. Monthly in-hand target copied unchanged: ₹{:,.2f}.".format(flt(calc_doc.target_net_salary))
    calc_doc.save(ignore_permissions=True)
    return {"job_offer": offer.name, "already_created": False}
