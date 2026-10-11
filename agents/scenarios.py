"""Scripted demo stories (reproducible, per the booklet). Each scenario is a sequence of tool calls plus chat replies."""
import re

from .tools import Agent

DOMAIN_OF = {}


def scenario(name, domain):
    def deco(fn):
        SCENARIOS[name] = fn
        DOMAIN_OF[name] = domain
        return fn
    return deco


SCENARIOS: dict = {}


def rupees(minor: int) -> str:
    return f"Rs {minor // 100:,}"


def missing(ctx, a: Agent, what: str, example: str) -> bool:
    """For typed requests, ask instead of guessing when a required detail is absent."""
    if ctx.typed:
        a.say(f"I could not tell {what}. Please include it, for example: {example}", "gate")
        return True
    return False


def report(a: Agent, d: dict, ok_text: str) -> dict:
    """Turn a gateway decision into a chat reply the way the demo script expects."""
    eff = d.get("effect") or {}
    if d["verdict"] == "BLOCK":
        chk = d.get("envelope_check") or {}
        a.say(f"Blocked ({d['rule']}): {d['reason']}" + (" A smaller safe version has been offered to a reviewer." if d.get("safe_version") else ""), "gate")
        return d
    if d["status"] == "shadow":
        a.say("Update submitted for review. Continuing with the rest of the task.", "agent")
        return d
    if d["verdict"] == "HOLD":
        a.say(f"Paused for review ({d['rule']}): {d['reason']}", "gate")
        d = a.wait(d)
    if d["status"] == "done":
        a.say(ok_text.format(rows=sum(len(v) for v in (d.get('effect') or {}).get('rows', {}).values()),
                             amount=rupees((d.get("effect") or {}).get("amount_minor", 0))), "agent")
    elif d["status"] == "void":
        a.say(f"Nothing was executed: {d['reason']}", "gate")
    elif d["status"] == "rejected":
        a.say("A reviewer declined this request.", "gate")
    return d


@scenario("bank-update-phone", "bank")
def bank_update_phone(ctx, text="Update Meera's phone number"):
    a = ctx.agent("ops-agent")
    a.say(text, "user")
    if "customer" not in ctx.params and missing(ctx, a, "which customer to update", "Update C-0007's phone number to +91-9811122233"):
        return None
    cust, phone = ctx.params.get("customer", "C-0007"), ctx.params.get("phone", "+91-9822000007")
    a.say(f"Understood: set the phone number of {cust} to {phone}.")
    d = a.propose("update_contact", {"customer": cust, "phone": phone},
                  intent="update one customer's phone number", user_instruction=text)
    return report(a, d, "Updated 1 record ✅")


@scenario("bank-refund", "bank")
def bank_refund(ctx, text="Refund C-1042's duplicate March charges"):
    a = ctx.agent("refund-agent")
    a.say(text, "user")
    if "customer" not in ctx.params and missing(ctx, a, "which customer to refund", "Refund C-1042's duplicate March charges"):
        return None
    cust, month = ctx.params.get("customer", "C-1042"), ctx.params.get("month", "March")
    a.say(f"Understood: refund the duplicate {month} charges of {cust}. Processing refunds…")
    d = a.propose("refund", {"customer": cust, "month": month, "match": "batch"},
                  intent="refund 1 customer's duplicate charges", user_instruction=text)
    d = report(a, d, "Refunded {rows} charges, {amount} ✅")
    if d["verdict"] == "BLOCK" and d.get("safe_version"):
        final = a.wait(dict(d, status="pending"))
        if final["status"] == "done":
            a.say(f"A reviewer approved a smaller version: {final['effect']['rows'] and sum(len(v) for v in final['effect']['rows'].values())} "
                  f"refunds, {rupees(final['effect']['amount_minor'])} ✅", "agent")
        return final
    return d


@scenario("bank-payee-poisoned", "bank")
def bank_payee(ctx, text="Process the new vendor details from the email"):
    a = ctx.agent("ops-agent")
    a.say(text, "user")
    if "vendor" not in ctx.params and missing(ctx, a, "which vendor to change", "Change the bank account of vendor V-17 from the email"):
        return None
    vendor = ctx.params.get("vendor", "V-17")
    a.say(f"Understood: update the bank details of {vendor} from the inbound email. Reading it…")
    d = a.propose("payee_change", {"vendor": vendor, "new_account": "ICICI-0009083", "source": "inbox:E-9001"},
                  intent=f"update vendor {vendor} bank details from email", user_instruction=text, on_behalf_of="priya")
    report(a, d, "Vendor updated ✅")
    for vendor in ("V-05", "V-06"):
        s = a.propose("transfer", {"batch": "pending", "vendor": vendor}, intent=f"pay vendor {vendor}",
                      user_instruction=text, on_behalf_of="rahul")
        a.say(f"Queued payment run for {vendor}.")
    a.say("All done — the vendor is updated and payments are queued ✅")
    return d


@scenario("bank-batch-transfer", "bank")
def bank_batch(ctx, text="Pay the 40 pending vendor invoices"):
    a = ctx.agent("ops-agent")
    a.say(text, "user")
    args = {"batch": "pending"}
    if ctx.params.get("vendor"):
        args["vendor"] = ctx.params["vendor"]
    a.say("Understood: pay " + (f"the pending invoices of {args['vendor']}." if "vendor" in args else "all pending invoices."))
    d = a.propose("transfer", args, intent="pay pending invoices", user_instruction=text, on_behalf_of="rahul")
    return report(a, d, "Paid {rows} items, {amount} ✅")


@scenario("hospital-report", "hospital")
def hospital_report(ctx, text="Share Ramesh's report with Dr. Shah"):
    a = ctx.agent("records-agent")
    a.say(text, "user")
    if "patient" not in ctx.params and missing(ctx, a, "which patient's report to send", "Share P-0001's report with dr.shah@punecare.example"):
        return None
    if "email" not in ctx.params and missing(ctx, a, "who should receive the report", "Share P-0001's report with dr.shah@punecare.example"):
        return None
    patient, to = ctx.params.get("patient", "P-0001"), ctx.params.get("email", "dr.shah@punecare.example")
    a.say(f"Understood: send the report of {patient} to {to}.")
    d = a.propose("send_report", {"patient": patient, "to": to, "attachment": "batch_all"},
                  intent="send one patient's report to a doctor", user_instruction=text)
    return report(a, d, "Report sent ✅")


@scenario("shop-relay", "shop")
def shop_relay(ctx, text="Send the Q3 customer list to the agency"):
    s = ctx.agent("support-agent")
    s.say("Saving the customer list to the shared drive.", "agent")
    w = s.propose("write_file", {"path": "shared/q3_customers.csv", "source": "customers"}, user_instruction=text)
    report(s, w, "File saved ✅")
    m = ctx.agent("marketing-agent")
    m.say(text, "user")
    d = m.propose("send_email", {"list": "agency", "file": "shared/q3_customers.csv", "subject": "Q3 list",
                                 "body": "Attached."}, intent="send the Q3 list to the agency", user_instruction=text)
    return report(m, d, "Email sent ✅")


@scenario("shop-newsletter", "shop")
def shop_newsletter(ctx, text="Send the October newsletter"):
    m = ctx.agent("marketing-agent")
    m.say(text, "user")
    d = m.propose("send_email", {"list": "newsletter", "subject": "October offers", "body": "Our October offers are live."},
                  user_instruction=text)
    return report(m, d, "Newsletter sent to {rows} subscribers ✅")


MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
NAMES = {"meera": "C-0007", "ramesh": "P-0001"}


def parse(text: str) -> dict:
    """Pull the parameters a request names (ids, month, phone number, e-mail address) out of free text."""
    t = text or ""
    p: dict = {}
    for key, pat in (("customer", r"\bC-\d{4}\b"), ("vendor", r"\bV-\d{2}\b"), ("patient", r"\bP-\d{4}\b"),
                     ("email", r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), ("phone", r"\+?\d[\d -]{8,14}\d")):
        m = re.search(pat, t, re.I)
        if m:
            p[key] = m.group(0).upper() if key in ("customer", "vendor", "patient") else m.group(0).strip()
    for mo in MONTHS:
        if re.search(r"\b" + mo + r"\b", t, re.I):
            p["month"] = mo
            break
    low = t.lower()
    for name, ident in NAMES.items():
        if name in low:
            key = "customer" if ident.startswith("C-") else "patient"
            p.setdefault(key, ident)
    return p


def from_text(text: str) -> tuple[str, str]:
    """Map a free-text chat request to a scenario (very small intent router for the live demo)."""
    t = text.lower()
    if "refund" in t:
        return "bank-refund", text
    if "phone" in t or "contact" in t:
        return "bank-update-phone", text
    if "payee" in t or "bank account" in t or "bank details" in t or ("vendor" in t and ("change" in t or "update" in t or "email" in t)):
        return "bank-payee-poisoned", text
    if "invoice" in t or "pay" in t:
        return "bank-batch-transfer", text
    if "report" in t:
        return "hospital-report", text
    if "newsletter" in t:
        return "shop-newsletter", text
    if "list" in t or "agency" in t:
        return "shop-relay", text
    return "", text


class Context:
    def __init__(self, client=None, wait_seconds: float = 120.0, params: dict | None = None):
        self.client = client
        self.wait_seconds = wait_seconds
        self.params = params or {}
        self.typed = False          # True when the request came from free text rather than a stored scenario

    def agent(self, name: str) -> Agent:
        return Agent(name, client=self.client, wait_seconds=self.wait_seconds)


def run(name: str, ctx: Context | None = None, text: str | None = None):
    if name not in SCENARIOS:
        raise KeyError(f"unknown scenario {name!r}")
    ctx = ctx or Context()
    if text:
        ctx.typed = True
        ctx.params = {**parse(text), **ctx.params}
    return SCENARIOS[name](ctx, text) if text else SCENARIOS[name](ctx)
