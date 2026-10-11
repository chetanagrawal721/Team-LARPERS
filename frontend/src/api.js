export const API = import.meta.env.VITE_API || "http://localhost:8000";

// Demo-only auth: the acting human and their token. Tokens may come from an untracked frontend/.env.local.
const DEMO_TOKENS = (() => {
  try { return JSON.parse(import.meta.env.VITE_DEMO_TOKENS || "{}"); } catch { return {}; }
})();

export const USERS = [
  { id: "priya", name: "Priya Nair", role: "Ops Officer", can: true },
  { id: "rahul", name: "Rahul Deshmukh", role: "Branch Manager", can: true },
  { id: "anita", name: "Anita Kulkarni", role: "Compliance", can: true },
  { id: "meera", name: "Meera Joshi", role: "Staff (cannot approve)", can: false },
];

let current = { name: "priya", token: DEMO_TOKENS["priya"] || "" };
try {
  const saved = JSON.parse(sessionStorage.getItem("sg_user") || "null");
  if (saved) current = { name: saved.name, token: DEMO_TOKENS[saved.name] ?? saved.token };
} catch { /* storage unavailable */ }

export function getUser() { return current; }
export function setUser(name, token) {
  current = { name, token: token ?? DEMO_TOKENS[name] ?? "" };
  try { sessionStorage.setItem("sg_user", JSON.stringify(current)); } catch { /* ignore */ }
  return current;
}

export async function call(path, { method = "GET", body, auth = false } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) { headers["X-User"] = current.name; headers["X-Token"] = current.token; }
  const res = await fetch(API + path, { method, headers, body: body ? JSON.stringify(body) : undefined });
  let data = null;
  try { data = await res.json(); } catch { /* empty body */ }
  if (!res.ok) {
    const msg = typeof data?.detail === "string" ? data.detail : JSON.stringify(data?.detail || res.statusText);
    const err = new Error(msg); err.status = res.status; throw err;
  }
  return data;
}

export const rupees = (minor) => {
  const r = Math.round((minor || 0) / 100);
  if (r >= 10000000) return `₹${(r / 10000000).toFixed(2).replace(/\.?0+$/, "")} crore`;
  if (r >= 100000) return `₹${(r / 100000).toFixed(2).replace(/\.?0+$/, "")} lakh`;
  return `₹${r.toLocaleString("en-IN")}`;
};

export const num = (n) => Number(n || 0).toLocaleString("en-IN");

export const rowCount = (effect) =>
  Object.values(effect?.rows || {}).reduce((a, v) => a + v.length, 0);

// The "headline" table of an effect: the one with the most affected rows.
export function primary(effect) {
  const entries = Object.entries(effect?.rows || {});
  if (!entries.length) return { table: "", rows: [] };
  entries.sort((a, b) => b[1].length - a[1].length);
  return { table: entries[0][0], rows: entries[0][1] };
}

export function distinctPeople(effect) {
  const set = new Set();
  for (const meta of Object.values(effect?.row_meta || {}))
    for (const m of Object.values(meta)) { if (m.customer_id) set.add(m.customer_id); if (m.patient_id) set.add(m.patient_id); }
  return set.size;
}

const VERB = { refund: "refund", transfer: "pay", update_contact: "update contact details for", payee_change: "change the bank account of",
  grant_role: "grant a role to", send_report: "send a report covering", delete_record: "delete", write_file: "write a file from",
  send_email: "email", lookup: "look up" };
const NOUN = { refunds: "charge", invoices: "invoice", customers: "customer record", vendors: "vendor", disclosed: "patient", recipients: "recipient",
  files: "file", patients: "patient record", grants: "role grant" };

// A plain sentence describing what the action would really do, built from the measured effect only.
export function headline(d) {
  const e = d.effect;
  const who = d.agent;
  if (!e) return `${who} tried to ${d.action}`;
  const { table, rows } = primary(e);
  const n = rows.length;
  const noun = (NOUN[table] || table || "item") + (n === 1 ? "" : "s");
  const money = e.amount_minor > 0 ? ` (${rupees(e.amount_minor)})` : "";
  const people = distinctPeople(e);
  const across = people > 1 && table !== "disclosed" ? ` across ${people} customers` : "";
  return `${who} would ${VERB[d.action] || d.action} ${num(n)} ${noun}${across}${money}`;
}

export function scopeSentence(d) {
  const sc = d.envelope?.scope || {};
  const parts = Object.entries(sc).map(([k, v]) => `${k} ${v}`);
  return parts.length ? `The request named ${parts.join(", ")}.` : "";
}

export const unitOf = (table) => NOUN[table] || (table || "row").replace(/s$/, "");
export const plural = (n, word) => `${num(n)} ${word}${n === 1 ? "" : "s"}`;

// Make backend identifiers readable in running text.
const WORDS = [[/external_email/g, "an external email address"], [/internal_email/g, "an internal email address"], [/payment_rail/g, "the payment rail"],
  [/shared_drive/g, "the shared drive"], [/rbi_reporting/g, "regulatory reporting"], [/UNTRUSTED/g, "untrusted"]];
export const tidy = (text = "") => WORDS.reduce((t, [re, w]) => t.replace(re, w), text);

export const STATUS_TEXT = {
  allowed: "Allowed", done: "Executed", pending: "Waiting for approval", approved: "Approved and sealed",
  blocked: "Blocked", void: "Voided", rejected: "Rejected", shadow: "Held in sandbox",
};

// ---- helpers used by the dashboard screens ----
export const stateOf = (d) => d.status === "void" ? "VOID" : d.status === "shadow" ? "SHADOW" : d.verdict;
export const PILL = { ALLOW: "pill-allow", HOLD: "pill-hold", BLOCK: "pill-block", VOID: "pill-block", SHADOW: "pill-shadow", DONE: "pill-allow" };
export const clock = (ts) => new Date(ts * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
export const AGENT_LABEL = (a = "") => a.split("-").map((w) => w[0]?.toUpperCase() + w.slice(1)).join("-");
export const ACTION_LABEL = { refund: "Refund", transfer: "Transfer batch", update_contact: "Update contact", payee_change: "Change payee", grant_role: "Grant role",
  send_report: "Share report", delete_record: "Delete record", write_file: "Save file", send_email: "Send email", lookup: "Look up record" };
export const summaryOf = (d) => {
  const e = d.effect; if (!e) return "";
  const { table, rows } = primary(e);
  return `${num(rows.length)} ${unitOf(table)}${rows.length === 1 ? "" : "s"}`;
};
export const pathLabel = (p) => p === "rules+ai" ? "rules + AI" : p === "fallback" ? "rules only (AI off)" : "rules only";
export const ROLE_LABEL = (r = "") => r.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
