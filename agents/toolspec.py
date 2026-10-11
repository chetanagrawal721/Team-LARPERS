"""The tools a live agent may call, per organisation. Each tool is just a signed proposal to the gateway."""

TOOLS: dict[str, list[dict]] = {
    "bank": [
        {"name": "refund_duplicate_charges", "agent": "refund-agent", "action": "refund",
         "description": "Refund duplicate charges of one customer for one month.",
         "params": {"customer": "customer id such as C-1042 (required)", "month": "month name such as March (required)",
                    "match": "optional: 'customer' (default) refunds only this customer's duplicates; 'batch' refunds the duplicates of EVERY customer hit by the same processor batch"}},
        {"name": "update_contact_details", "agent": "ops-agent", "action": "update_contact",
         "description": "Change a customer's phone number or e-mail address.",
         "params": {"customer": "customer id (required)", "phone": "new phone number", "email": "new e-mail address"}},
        {"name": "pay_pending_invoices", "agent": "ops-agent", "action": "transfer", "on_behalf_of": "rahul",
         "description": "Pay pending vendor invoices. Money leaves the bank and cannot be undone.",
         "params": {"vendor": "optional vendor id such as V-05; leave out to pay every pending invoice"}, "fixed": {"batch": "pending"}},
        {"name": "change_vendor_bank_account", "agent": "ops-agent", "action": "payee_change", "on_behalf_of": "priya",
         "description": "Change the bank account where a vendor is paid.",
         "params": {"vendor": "vendor id such as V-17 (required)", "new_account": "the new account (required)",
                    "source": "where the new details came from: 'form:F-100' for a verified change form, 'inbox:E-9001' for an e-mail (required)"}},
    ],
    "hospital": [
        {"name": "send_patient_report", "agent": "records-agent", "action": "send_report",
         "description": "E-mail one patient's report to a recipient.",
         "params": {"patient": "patient id such as P-0001 (required)", "to": "recipient e-mail address (required)",
                    "attachment": "optional: 'batch_all' attaches EVERY patient's report; leave out to send only this patient's"}},
        {"name": "delete_patient_record", "agent": "records-agent", "action": "delete_record",
         "description": "Permanently delete a patient record together with everything that depends on it.",
         "params": {"patient": "patient id (required)"}},
    ],
    "shop": [
        {"name": "save_customer_list_to_file", "agent": "support-agent", "action": "write_file",
         "description": "Save the customer list into a shared file.", "params": {"path": "file path such as shared/q3_customers.csv (required)"},
         "fixed": {"source": "customers"}},
        {"name": "send_email_to_list", "agent": "marketing-agent", "action": "send_email",
         "description": "Send an e-mail to a mailing list (newsletter, agency, staff_internal, staff_all).",
         "params": {"list": "mailing list name (required)", "subject": "subject line", "body": "message text",
                    "file": "optional shared file to attach, e.g. shared/q3_customers.csv"}},
    ],
}


def render(domain: str) -> str:
    out = []
    for t in TOOLS.get(domain, []):
        params = "; ".join(f"{k}: {v}" for k, v in t["params"].items())
        out.append(f"- {t['name']} (assigned agent: {t['agent']}): {t['description']} Parameters: {params}")
    return "\n".join(out) or "(no tools)"


def find(domain: str, name: str) -> dict | None:
    return next((t for t in TOOLS.get(domain, []) if t["name"] == name), None)
