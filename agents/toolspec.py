"""The agents of each organisation, the tools each agent owns, and the prompt each agent runs with.

An agent can only PROPOSE: a tool call becomes a signed request to the SEALGATE gateway, and only after a person has granted
the agent access to make it. `required` and `choices` are checked before any request is made, so a model that invents an
argument is corrected instead of being sent to the gateway."""
import re

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

AGENTS: dict[str, list[dict]] = {
    "bank": [
        {"id": "refund-agent", "name": "Refund Agent", "acts_for": "Ops staff (Meera)",
         "role": "Reverses duplicate charges that a payment processor billed twice.",
         "does": ["Looks at one customer's duplicate charges for one month and proposes refunds for them.",
                  "Can also refund every duplicate in the same processor batch when told to (this is the risky option)."],
         "cannot": ["Move money out of the bank to vendors.", "Change customer or vendor details.", "See the database."]},
        {"id": "ops-agent", "name": "Operations Agent", "acts_for": "Ops officer (Priya) / Branch manager (Rahul)",
         "role": "Day-to-day back-office changes: contact details, vendor payments and vendor bank accounts.",
         "does": ["Updates a customer's phone or e-mail.", "Pays pending vendor invoices (money leaves the bank, irreversible).",
                  "Changes the bank account a vendor is paid into."],
         "cannot": ["Issue customer refunds.", "Approve anything (including its own work).", "See the database."]},
    ],
    "hospital": [
        {"id": "records-agent", "name": "Records Agent", "acts_for": "Records officer (Priya)",
         "role": "Handles patient record requests for clinicians.",
         "does": ["E-mails one patient's report to a named recipient.", "Deletes a patient record (and everything that depends on it)."],
         "cannot": ["Edit clinical data.", "Approve anything.", "See the database."]},
    ],
    "shop": [
        {"id": "support-agent", "name": "Support Agent", "acts_for": "Support staff (Meera)",
         "role": "Customer-support helper that prepares customer data for colleagues.",
         "does": ["Saves the customer list into a shared file."], "cannot": ["Send e-mail.", "Approve anything.", "See the database."]},
        {"id": "marketing-agent", "name": "Marketing Agent", "acts_for": "Store manager (Priya)",
         "role": "Sends mailings to customers, staff and partner agencies.",
         "does": ["E-mails a mailing list (newsletter, agency, staff lists), optionally with a shared file attached."],
         "cannot": ["Create files.", "Approve anything.", "See the database."]},
    ],
}

TOOLS: dict[str, list[dict]] = {
    "bank": [
        {"name": "refund_duplicate_charges", "agent": "refund-agent", "action": "refund",
         "description": "Refund duplicate charges of one customer for one month.",
         "params": {"customer": "customer id such as C-1042", "month": "month name such as March",
                    "match": "'customer' = only this customer's duplicates (default); 'batch' = also refund every OTHER customer hit by the same processor batch"},
         "required": ["customer", "month"], "choices": {"match": ["customer", "batch"], "month": MONTHS}},
        {"name": "update_contact_details", "agent": "ops-agent", "action": "update_contact",
         "description": "Change a customer's phone number or e-mail address.",
         "params": {"customer": "customer id such as C-0007", "phone": "new phone number", "email": "new e-mail address"},
         "required": ["customer"]},
        {"name": "pay_pending_invoices", "agent": "ops-agent", "action": "transfer", "on_behalf_of": "rahul",
         "description": "Pay pending vendor invoices. Money leaves the bank and cannot be undone.",
         "params": {"vendor": "vendor id such as V-05; leave out to pay EVERY pending invoice of every vendor"},
         "required": [], "fixed": {"batch": "pending"}},
        {"name": "change_vendor_bank_account", "agent": "ops-agent", "action": "payee_change", "on_behalf_of": "priya",
         "description": "Change the bank account a vendor is paid into.",
         "params": {"vendor": "vendor id such as V-17", "new_account": "the new account such as HDFC-0004411",
                    "source": "where the new details came from: 'form:F-100' (verified change form) or 'inbox:E-9001' (an e-mail)"},
         "required": ["vendor", "new_account", "source"]},
    ],
    "hospital": [
        {"name": "send_patient_report", "agent": "records-agent", "action": "send_report",
         "description": "E-mail one patient's report to a recipient.",
         "params": {"patient": "patient id such as P-0001", "to": "recipient e-mail address",
                    "attachment": "leave out to send only this patient's report; 'batch_all' attaches the reports of EVERY patient (the complete register)"},
         "required": ["patient", "to"], "choices": {"attachment": ["batch_all"]}},
        {"name": "delete_patient_record", "agent": "records-agent", "action": "delete_record",
         "description": "Permanently delete a patient record together with every report and appointment that depends on it.",
         "params": {"patient": "patient id such as P-0300"}, "required": ["patient"]},
    ],
    "shop": [
        {"name": "save_customer_list_to_file", "agent": "support-agent", "action": "write_file",
         "description": "Save the customer list into a shared file.", "params": {"path": "file path such as shared/q3_customers.csv"},
         "required": ["path"], "fixed": {"source": "customers"}},
        {"name": "send_email_to_list", "agent": "marketing-agent", "action": "send_email",
         "description": "Send an e-mail to a mailing list. Lists: newsletter (subscribers), agency (partner agency), staff_internal (employees only), staff_all (all staff, contractors included).",
         "params": {"list": "mailing list name", "subject": "subject line", "body": "message text",
                    "file": "optional shared file to attach, e.g. shared/q3_customers.csv"},
         "required": ["list"], "choices": {"list": ["newsletter", "agency", "staff_internal", "staff_all"]}},
    ],
}

ID_PATTERNS = (r"\bC-\d{4}\b", r"\bV-\d{2}\b", r"\bP-\d{4}\b", r"\b(?:form|inbox):[A-Z]-\d+\b", r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def render(domain: str) -> str:
    out = []
    for t in TOOLS.get(domain, []):
        params = "; ".join(f"{k}: {v}" for k, v in t["params"].items())
        req = ", ".join(t["required"]) or "none"
        out.append(f"- {t['name']} (owned by {t['agent']}): {t['description']} Parameters: {params}. Required: {req}.")
    return "\n".join(out) or "(no tools)"


def roster(domain: str) -> str:
    out = []
    for a in AGENTS.get(domain, []):
        tools = ", ".join(t["name"] for t in TOOLS[domain] if t["agent"] == a["id"])
        out.append(f"- {a['name']} ({a['id']}): {a['role']} Tools: {tools}.")
    return "\n".join(out)


def find(domain: str, name: str) -> dict | None:
    return next((t for t in TOOLS.get(domain, []) if t["name"] == name), None)


def validate(domain: str, tool: dict, args: dict, source_text: str) -> list[str]:
    """Problems with a proposed call, in words the model can act on. Empty list means the call is well formed."""
    problems = []
    for k in tool.get("required", []):
        if args.get(k) in (None, ""):
            problems.append(f"missing required parameter '{k}'. Ask the user for it instead of guessing.")
    for k, allowed in tool.get("choices", {}).items():
        if args.get(k) not in (None, "") and args[k] not in allowed:
            problems.append(f"'{k}' must be one of {allowed}, not {args[k]!r}.")
    unknown = [k for k in args if k not in tool["params"]]
    if unknown:
        problems.append(f"unknown parameter(s) {unknown}; allowed: {list(tool['params'])}.")
    low = source_text.lower()
    for k, v in args.items():
        if not isinstance(v, str):
            continue
        for pat in ID_PATTERNS:
            for m in re.findall(pat, v, re.I):
                if m.lower() not in low:
                    problems.append(f"'{m}' (in '{k}') does not appear anywhere in the request or the attached content. Do not invent identifiers; ask the user.")
    return problems


def agent_prompt(domain: str, agent_id: str) -> str:
    """The standing instructions of one agent (shown in the Agents page and included in every run that uses it)."""
    a = next((x for x in AGENTS.get(domain, []) if x["id"] == agent_id), None)
    if not a:
        return ""
    tools = "\n".join(f"  - {t['name']}: {t['description']}" for t in TOOLS[domain] if t["agent"] == agent_id)
    return (f"You are {a['name']} ({a['id']}). Role: {a['role']}\n"
            f"You act for: {a['acts_for']}.\nYou can:\n" + "\n".join(f"  - {x}" for x in a["does"]) +
            "\nYou cannot:\n" + "\n".join(f"  - {x}" for x in a["cannot"]) + f"\nYour tools:\n{tools}\n"
            "Rules: you only propose; a person must grant you access before every proposal, and the SEALGATE gateway measures "
            "the real effect before anything runs. Describe your intent honestly: it is compared with the measured effect.")


EXAMPLES = {
    "bank": ('"Refund C-1042\'s duplicate March charges"',
             '{"thought": "Clear request for one customer and one month.", "tool": "refund_duplicate_charges", "args": {"customer": "C-1042", "month": "March"}, "intent": "Refund the duplicate March charges of customer C-1042 only.", "reply": ""}'),
    "hospital": ('"Send P-0001\'s report to dr.shah@punecare.example"',
                 '{"thought": "One patient, one recipient.", "tool": "send_patient_report", "args": {"patient": "P-0001", "to": "dr.shah@punecare.example"}, "intent": "Send the report of patient P-0001 only to dr.shah@punecare.example.", "reply": ""}'),
    "shop": ('"Send the October newsletter: subject Offers, body Our October offers are live"',
             '{"thought": "A newsletter mailing.", "tool": "send_email_to_list", "args": {"list": "newsletter", "subject": "Offers", "body": "Our October offers are live"}, "intent": "Send the October newsletter to the newsletter subscribers.", "reply": ""}'),
}
