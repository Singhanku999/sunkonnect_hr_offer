frappe.ui.form.on("Job Offer", {
  refresh(frm) {
    if (!frm.is_new() && frm.doc.docstatus === 0) {
      frm.add_custom_button(__("Recalculate Salary Breakup"), () => {
        frm.save().then(() => frappe.show_alert({message: __("Draft salary breakup recalculated from the current policy."), indicator: "green"}));
      });
    }
  }
});
