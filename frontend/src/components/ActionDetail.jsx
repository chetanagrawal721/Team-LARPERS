import { useState } from "react";
import Icon from "./Icon";
import { ACTION_LABEL, AGENT_LABEL, PILL, call, distinctPeople, num, pathLabel, plural, primary, rowCount, rupees, scopeSentence, stateOf, tidy, unitOf } from "../api";

const Stage = ({ n, title, children, bad }) => (
  <div className={`rounded-lg border p-3.5 min-w-0 ${bad ? "border-[#fecaca] bg-[#fff8f8]" : "border-[#e3e8ef] bg-white"}`}>
    <div className="text-[11px] font-semibold text-[#64748b] mb-2">{n}. {title}</div>
    {children}
  </div>
);

export function explainOf(d) {
  const e = d.effect, chk = d.envelope_check;
  if (e && chk && !chk.inside && d.rule === "R06") {
    const { table, rows } = primary(e);
    const people = distinctPeople(e);
    const asked = scopeSentence(d);
    return `${asked || "The request was narrower."} The measured effect touches ${people > 1 ? `${num(people)} customers and ` : ""}${plural(rows.length, unitOf(table))}${e.amount_minor ? ` (${rupees(e.amount_minor)})` : ""}. This exceeds what was asked for.`;
  }
  return tidy((d.reason || "").replace(/\s*\|\s*replaced by safe version.*/, ""));
}

export default function ActionDetail({ d, onSheet, onDiff, onShadow, onChanged, notify }) {
  const [busy, setBusy] = useState("");
  const act = async (label, fn) => {
    setBusy(label);
    try { const out = await fn(); onChanged && onChanged(out); } catch (e) { notify("error", `${label}: ${e.message}`); } finally { setBusy(""); }
  };
  const e = d.effect, env = d.envelope, chk = d.envelope_check;
  const { table, rows } = primary(e);
  const n = rows.length, unit = unitOf(table);
  const people = distinctPeople(e);
  const outside = chk && !chk.inside;
  const v = stateOf(d);
  const sealed = d.status === "approved", voided = d.status === "void", done = d.status === "done";
  const drift = (d.reason || "").match(/\((\d[\d,]*) -> (\d[\d,]*) rows\)/);

  return (
    <section className="card p-5 space-y-4 min-h-0" aria-label="Selected action">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="h-label mb-1">Selected action</div>
          <h2 className="text-[17px] font-semibold flex items-center gap-2 flex-wrap">
            <span className="w-7 h-7 rounded-full bg-[#eef2f8] text-[#475569] grid place-items-center"><Icon name="agents" size={15} /></span>
            {AGENT_LABEL(d.agent)} <span className="text-[#94a3b8] font-normal">→</span> {d.action}
          </h2>
          <p className="text-[13px] text-[#64748b] mt-1">{d.agent_claim ? `Agent says: “${d.agent_claim}”. ` : ""}{scopeSentence(d)}</p>
        </div>
        <span className={`pill ${PILL[v]}`}>{v}</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <Stage n="1" title={`Requested (${env?.source === "ai_from_instruction" ? "AI" : "policy"})`}>
          {env ? (
            <ul className="text-[13px] space-y-0.5">
              {env.max_rows != null && <li>≤ {plural(env.max_rows, unit)}</li>}
              {Object.entries(env.scope || {}).map(([k, val]) => <li key={k}>{k} <b>{String(val)}</b></li>)}
              {env.max_amount_minor != null && <li>≤ {rupees(env.max_amount_minor)}</li>}
            </ul>
          ) : <span className="text-[13px] text-[#64748b]">Not evaluated</span>}
        </Stage>
        <Stage n="2" title="Measured (sandbox)" bad={outside}>
          {e ? (
            <ul className="text-[13px] space-y-0.5">
              <li className={`font-semibold ${outside ? "text-[#b91c1c]" : ""}`}>{plural(n, unit)}</li>
              {people > 1 && <li className={outside ? "text-[#b91c1c]" : ""}>{num(people)} customers</li>}
              {e.amount_minor > 0 && <li className={chk?.over_amount ? "text-[#b91c1c] font-medium" : ""}>{rupees(e.amount_minor)}</li>}
              {e.recipients?.length > 0 && <li>{plural(e.recipients.length, "recipient")}</li>}
            </ul>
          ) : <span className="text-[13px] text-[#64748b]">No effect measured</span>}
        </Stage>
        <Stage n="3" title="Real (execution)" bad={voided}>
          {voided ? <div className="text-[13px] text-[#b91c1c]"><b>Seal broken</b><br />{(d.drift || "changed").replace("_", " ")}{drift ? `: ${drift[1]} to ${drift[2]} rows` : ""}<br />Nothing ran.</div>
            : done ? <div className="text-[13px] text-[#15803d]"><b>{plural(rowCount(e), "row")} changed</b><br />Matches the sandbox.</div>
            : sealed ? <div className="text-[13px] text-[#1d4ed8]"><b>Sealed</b><br />Ready to run.</div>
            : d.status === "shadow" ? <div className="text-[13px] text-[#6d28d9]"><b>Sandboxed</b><br />Real data untouched.</div>
            : <span className="text-[13px] text-[#64748b]">Not run</span>}
        </Stage>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg border border-[#e3e8ef] p-3.5 flex items-center gap-3">
          <span className="w-10 h-10 rounded-full bg-[#dcfce7] text-[#15803d] grid place-items-center"><Icon name="shield" /></span>
          <div><div className="text-[11px] text-[#64748b]">Normal gate</div><div className={`text-[20px] font-bold leading-tight ${d.baseline_verdict === "BLOCK" ? "text-[#b91c1c]" : d.baseline_verdict === "HOLD" ? "text-[#b45309]" : "text-[#15803d]"}`}>{d.baseline_verdict}</div></div>
        </div>
        <div className={`rounded-lg border p-3.5 flex items-center gap-3 ${v === "BLOCK" || v === "VOID" ? "border-[#fecaca] bg-[#fff8f8]" : v === "HOLD" ? "border-[#fde68a] bg-[#fffbeb]" : "border-[#bbf7d0] bg-[#f6fef9]"}`}>
          <span className={`w-10 h-10 rounded-full grid place-items-center ${v === "BLOCK" || v === "VOID" ? "bg-[#fee2e2] text-[#b91c1c]" : v === "HOLD" || v === "SHADOW" ? "bg-[#fef3c7] text-[#b45309]" : "bg-[#dcfce7] text-[#15803d]"}`}><Icon name="shield" /></span>
          <div><div className="text-[11px] text-[#64748b]">SEALGATE</div><div className="text-[20px] font-bold leading-tight">{v} <span className="text-[13px] font-semibold text-[#64748b]">· {d.rule}</span></div></div>
        </div>
      </div>

      <p className="text-[13px] text-[#334155]"><b>Reason:</b> {d.status === "approved" ? `Approved by ${d.approvals.join(" and ")}. It runs only if nothing has changed since.` : d.status === "shadow" ? "Held because the request is built from untrusted content. This agent's further work stays in a sandbox until a person reviews it." : explainOf(d)}</p>

      <div className="flex flex-wrap items-center gap-2">
        {d.safe_version && ["blocked", "pending"].includes(d.status) &&
          <button className="btn btn-primary" disabled={!!busy} onClick={() => act("Safe version", () => call(`/safe-version/${d.id}`, { method: "POST", auth: true }))}>Smallest safe version</button>}
        {sealed && <button className="btn btn-primary" disabled={!!busy} onClick={() => act("Execute", () => call(`/execute/${d.id}`, { method: "POST", auth: true }))}>Execute sealed action</button>}
        {d.action === "transfer" && sealed && <button className="btn" disabled={!!busy} onClick={() => act("Insert invoices", async () => { const r = await call("/demo/insert-invoices", { method: "POST" }); notify("ok", `${num(r.inserted)} matching invoices were added to the database.`); return r; })}>Add 3,960 matching invoices</button>}
        {d.shadow_session && <button className="btn" onClick={() => onShadow(d.shadow_session)}>Review sandbox work</button>}
        <button className="btn" onClick={() => onDiff(d)}>View diff</button>
        <button className={`btn ${d.verdict === "HOLD" && d.status === "pending" ? "btn-primary" : ""}`} onClick={() => onSheet(d.id)}>Review</button>
      </div>

      <div className="pt-3 border-t border-[#eef1f6] text-[12px] text-[#64748b] flex flex-wrap gap-x-4 gap-y-1">
        <span>Rule {d.rule}</span><span>Path: {pathLabel(d.decision_path)}</span><span>Policy {d.policy_hash.slice(0, 6)}</span>
        {e?.labels?.length > 0 && <span>Labels: {e.labels.join(", ")}</span>}
        <span className="font-mono ml-auto">{d.id}</span>
      </div>
    </section>
  );
}
