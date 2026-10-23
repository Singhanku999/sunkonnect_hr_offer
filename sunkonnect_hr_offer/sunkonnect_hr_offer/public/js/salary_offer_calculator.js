frappe.ui.form.on("Salary Offer Calculator", {
  refresh(frm) {
    if (!frm.doc.job_offer) {
      frm.add_custom_button(__("Calculate CTC"), async () => {
        if (!frm.doc.designation || !frm.doc.target_net_salary) {
          frappe.msgprint(__("Select a designation and enter the monthly in-hand target first."));
          return;
        }
        if (frm.is_new()) await frm.save();
        const r = await frappe.call({
          method: "sunkonnect_hr_offer.salary_offer.calculate_pre_offer",
          args: {docname: frm.doc.name}
        });
        if (r.message) {
          Object.keys(r.message).forEach(k => { if (frm.fields_dict[k]) frm.set_value(k, r.message[k]); });
          await frm.save();
          frappe.show_alert({message: __("CTC calculated and saved."), indicator: "green"});
        }
      });
      if (frm.doc.negotiation_status === "Accepted") {
        frm.add_custom_button(__("Create Job Offer"), async () => {
          const r = await frappe.call({
            method: "sunkonnect_hr_offer.salary_offer.create_job_offer_from_calculator",
            args: {name: frm.doc.name}, freeze: true, freeze_message: __("Creating Job Offer...")
          });
          if (r.message && r.message.job_offer) {
            frappe.show_alert({message: __("Job Offer created: ") + r.message.job_offer, indicator: "green"});
            frm.reload_doc();
            frappe.set_route("Form", "Job Offer", r.message.job_offer);
          }
        }).addClass("btn-primary");
      }
    }
  },
  job_applicant(frm) {
    if (frm.doc.job_applicant) {
      frappe.db.get_value("Job Applicant", frm.doc.job_applicant, "applicant_name").then(r => {
        if (r && r.message) frm.set_value("applicant_name", r.message.applicant_name || "");
      });
    } else { frm.set_value("applicant_name", ""); }
  },
  designation(frm) {
    if (!frm.doc.designation) {
      ["budget_min_annual_ctc", "budget_max_annual_ctc", "budget_approved_positions", "budget_financial_year", "budget_note", "budget_status"].forEach(f => frm.set_value(f, ""));
      return;
    }
    frappe.call({method: "sunkonnect_hr_offer.salary_offer.fetch_designation_budget", args: {designation: frm.doc.designation}}).then(r => {
      const b = r.message || {};
      ["budget_min_annual_ctc", "budget_max_annual_ctc", "budget_approved_positions", "budget_financial_year", "budget_note"].forEach(f => frm.set_value(f, b[f] ?? ""));
      if (b.budget_slabs && b.budget_slabs.length > 1) {
        const rows = b.budget_slabs.map(x => `<tr><td>${frappe.utils.escape_html(x.financial_year || "-")}</td><td>${format_currency(x.min)}</td><td>${format_currency(x.max)}</td><td>${x.positions}</td></tr>`).join("");
        frappe.msgprint({title: __("Hiring Budget Slabs"), message: `<table class="table table-bordered"><thead><tr><th>FY</th><th>Min Annual CTC</th><th>Max Annual CTC</th><th>Approved Positions</th></tr></thead><tbody>${rows}</tbody></table>`});
      } else if (!b.budget_slabs || !b.budget_slabs.length) {
        frappe.msgprint(__("No hiring budget slab is configured for this designation. Add one in Salary Offer Policy."));
      }
    });
  },
  target_net_salary(frm) { frm.set_value("budget_status", "Calculate CTC to compare with the designation budget"); },
  variable_ctc_annual(frm) { frm.set_value("budget_status", "Calculate CTC to refresh the budget check"); }
});
