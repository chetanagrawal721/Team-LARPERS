export const API = import.meta.env.VITE_API || "http://localhost:8000";

// Demo-only auth: the acting human and their token. Tokens may come from an untracked frontend/.env.local.
const DEMO_TOKENS = (() => {
  try { return JSON.parse(import.meta.env.VITE_DEMO_TOKENS || "{}"); } catch { return {}; }
})();

export const USERS = ["priya", "rahul", "anita", "meera"];

let current = { name: "priya", token: DEMO_TOKENS["priya"] || "" };
try {
  const saved = JSON.parse(sessionStorage.getItem("sg_user") || "null");
  if (saved) current = saved;
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
  if (r >= 100000) return `₹${(r / 100000).toFixed(r >= 1000000 ? 1 : 2).replace(/\.?0+$/, "")} lakh`;
  return `₹${r.toLocaleString("en-IN")}`;
};

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

export const VERDICT_COLOR = { ALLOW: "text-emerald-400", HOLD: "text-amber-400", BLOCK: "text-rose-400", VOID: "text-rose-400", DONE: "text-emerald-400" };
