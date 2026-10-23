# Sunkonnect HR Offer Salary — starter implementation pack

This is a **starter app scaffold**, not yet installed on your ERPNext site. It maps the visible `Recruitment.xlsx` rules into an ERPNext v15 Job Offer workflow while leaving standard Job Applicant, Job Offer, Employee, Salary Structure and Salary Structure Assignment in place.

## Included
- Job Offer custom fields for target take-home, component values, compliance notes and annual CTC.
- Designation-to-wage mapping from rows 73–94 of the workbook.
- Editable Single DocType `Salary Offer Policy` with editable ratios, PF/ESI/bonus/LWF/gratuity settings, wage rates and designation mappings.
- Calculation service and candidate salary breakup Print Format HTML.
- Draft-only recalculation: submitted Job Offers are not overwritten by the validate hook.

## Important before production
1. Have your HR/payroll owner and CA verify the statutory values in the sheet (PF ceiling, ESI, bonus, LWF, minimum wages and Code on Wages test). The workbook itself labels several values as requiring verification. This code intentionally carries that warning into the calculation output.
2. The workbook's current wage rates are carried forward across FY 2026–27 months. Add effective dates / new notified rates when updated.
3. Frappe `Percent` fields are normalized from percentage points (e.g. 60) to decimals inside the calculation service. Confirm this behavior in your ERPNext v15 staging site before live use.
4. The salary calculator is a first pass and needs test cases against Excel-calculated outputs for multiple target salaries/designations before live offers. No production offer should be issued from this scaffold without parity testing.
5. This package does not alter standard payroll Salary Structures. After candidate acceptance and Employee creation, HR should create/assign the standard payroll Salary Structure.

## Install approach
Use a staging site first. Copy the `sunkonnect_hr_offer` app folder into a new app generated with `bench new-app sunkonnect_hr_offer`, merge the supplied files, then run `bench --site <staging-site> install-app sunkonnect_hr_offer` and `bench --site <staging-site> migrate`. Do not copy into production before test/parity review.

After install, open **Salary Offer Policy** and populate the designation mappings and wage rates. Create a **Job Offer** in Draft, enter `Target Monthly Take-home (before TDS)` and a designation, then save. The calculated custom fields are intended for the candidate print format.

## Next build steps
- Normalize Percent values and confirm currency rounding.
- Add a button that explicitly calculates without saving unrelated Job Offer changes.
- Register `candidate_salary_breakup.html` as a Print Format in the site (or use it to create a standard Print Format record).
- Add roles/permissions, tests against Excel, and snapshot/offer-revision policy.
- Add effective-date logic for wage rates and a separate approved/released snapshot flow.


## Added: pre-offer negotiation calculator and hiring budget slabs
- New **Salary Offer Calculator** DocType: used before creating a standard Job Offer. Link the Job Applicant, choose Company and Designation, enter the agreed monthly in-hand target and calculate the gross/CTC.
- New **Hiring Budget Slabs** child table in **Salary Offer Policy**: maintain a minimum/maximum annual CTC, approved positions, financial year and approval note per Designation. Selecting a designation on the calculator displays its budget; multiple slabs for the role are listed.
- The budget check flags packages below/above the configured range. Packages above budget are blocked from Job Offer conversion until the budget is updated/approved. This is a budget control, not an HR approval workflow.
- Mark negotiation **Accepted**, save, then click **Create Job Offer**. The same `target_net_salary` value is copied into `Job Offer.custom_target_net_salary`; the Job Offer validate hook recalculates the component snapshot from the current policy. The calculator records the resulting Job Offer to prevent duplicate conversion.
- Existing Job Offer salary fields and candidate breakup print format remain part of this app. Payroll Salary Structure / Salary Structure Assignment are not modified.

## Upgrade an existing local clone
Copy/merge this updated app folder into `apps/sunkonnect_hr_offer`, then run:
```bash
bench build --app sunkonnect_hr_offer
bench --site erpnext.local migrate
bench --site erpnext.local clear-cache
```
If the app is not installed on the site yet, run `bench --site erpnext.local install-app sunkonnect_hr_offer` after it is listed as a separate line in `sites/apps.txt`; then migrate and clear cache.

After migration, open **Salary Offer Policy** and add budget slabs for each designation. The budget feature is empty by default and intentionally does not invent company-approved CTC ranges. Configure HR-approved ranges before using the calculator.
