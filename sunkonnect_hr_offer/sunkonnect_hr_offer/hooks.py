app_name = "sunkonnect_hr_offer"
app_title = "Sunkonnect HR Offer Salary"
app_publisher = "Sunkonnect"
app_description = "Candidate-facing salary offer breakup for ERPNext"
app_email = "erp.support@sunkonnect.co"
app_license = "MIT"

after_install = "sunkonnect_hr_offer.install.after_install"
doc_events = {
    "Job Offer": {
        "validate": "sunkonnect_hr_offer.salary_offer.validate_job_offer"
    },
    "Salary Offer Calculator": {
        "validate": "sunkonnect_hr_offer.salary_offer.validate_pre_offer_calculator"
    }
}
doctype_js = {
    "Job Offer": "public/js/job_offer.js",
    "Salary Offer Calculator": "public/js/salary_offer_calculator.js"
}
