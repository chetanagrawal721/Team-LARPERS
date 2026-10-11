import { useState } from "react";
import Overlay from "./Overlay";
import { num, rupees, unitOf } from "../api";

const PAGE = 8;
const TITLE = { refunds: "Refunds affected", invoices: "Invoices affected", transactions: "Payments recorded", disclosed: "Patients disclosed", recipients: "Recipients",
  vendors: "Vendors changed", customers: "Customer records changed", files: "Files written", patients: "Patient records", reports: "Reports", appointments: "Appointments", grants: "Role grants" };

// Real / Sandbox / Difference with inside-the-request and outside-the-request rows.
export default function DiffOverlay({ d, onClose }) {
  const eff = d.effect;
  const tables = Object.keys(eff?.rows || {}).sort((a, b) => eff.rows[b].length - eff.rows[a].length);
  const [tab, setTab] = useState("diff");
  const [table, setTable] = useState(tables[0]);
  const [page, setPage] = useState(0);
  const [all, setAll] = useState(false);
  const offending = new Set((d.envelope_check?.offending_rows || {})[table] || []);
  const pks = eff?.rows?.[table] || [];
  const inside = pks.filter((p) => !offending.has(p)).length;
  const sorted = [...pks].sort((a, b) => Number(offending.has(a)) - Number(offending.has(b)) || a.localeCompare(b));
  const shown = all ? sorted : sorted.slice(page * PAGE, page * PAGE + PAGE);
  const pages = Math.ceil(sorted.length / PAGE);

  return (
    <Overlay title="Effect difference" onClose={onClose} width={820} subtitle={`${d.agent} → ${d.action}`}
             footer={<div className="flex justify-between items-center"><button className="btn" onClick={() => setAll(!all)}>{all ? "Show pages" : `View full list (${num(pks.length)})`}</button><button className="btn btn-primary" onClick={onClose}>Close</button></div>}>
      <div className="flex gap-6 border-b border-[#e3e8ef] mb-4" role="tablist">
        {[["real", "Real"], ["sandbox", "Sandbox"], ["diff", "Difference"]].map(([id, label]) => (
          <button key={id} role="tab" aria-selected={tab === id} className={`tab ${tab === id ? "tab-active" : ""}`} onClick={() => setTab(id)}>{label}</button>
        ))}
      </div>
      {!eff && <p className="text-[#64748b]">No effect was measured for this decision.</p>}
      {eff && tab === "real" && (
        <p className="text-[13px] text-[#334155]">{d.status === "done" ? "The real database now contains the changes shown under Sandbox, identical to the measured result." : "The real database is unchanged. Nothing has run."}</p>
      )}
      {eff && tab !== "real" && (
        <>
          <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
            <div className="font-semibold">{TITLE[table] || table}</div>
            {tab === "diff" && (
              <div className="flex gap-4 text-[13px]">
                <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#16a34a]" />Inside request <b>{num(inside)}</b></span>
                <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#dc2626]" />Outside request <b className="text-[#b91c1c]">{num(pks.length - inside)}</b></span>
              </div>
            )}
          </div>
          {tables.length > 1 && <div className="flex gap-2 mb-3 flex-wrap">{tables.map((t) => <button key={t} className={`chip ${t === table ? "bg-[#e8f0ff] border-[#bcd2ff] text-[#1d4ed8]" : "border-[#e3e8ef] text-[#475569]"}`} onClick={() => { setTable(t); setPage(0); }}>{TITLE[t] || t} ({num(eff.rows[t].length)})</button>)}</div>}
          <table className="w-full text-[13px]">
            <thead><tr className="text-left text-[11px] uppercase tracking-wider text-[#64748b] border-b border-[#e3e8ef]"><th className="py-2">{unitOf(table) === "refund" ? "Customer ID" : "ID"}</th><th>Name</th><th>Amount</th>{tab === "diff" && <th>Status</th>}</tr></thead>
            <tbody>
              {shown.map((pk) => {
                const m = eff.row_meta?.[table]?.[pk] || {}; const out = offending.has(pk);
                return (
                  <tr key={pk} className="border-b border-[#f1f4f8]">
                    <td className="py-2 font-mono text-[12px]">{m.customer_id || m.patient_id || m.vendor_id || pk}{(m.customer_id || m.vendor_id) && <span className="text-[#94a3b8]"> · {pk}</span>}</td>
                    <td>{m.name || ""}</td>
                    <td>{m.amount_minor != null ? rupees(m.amount_minor) : ""}</td>
                    {tab === "diff" && <td><span className={`pill ${out ? "pill-block" : "pill-allow"}`}>{out ? "Outside" : "Inside"}</span></td>}
                  </tr>
                );
              })}
            </tbody>
          </table>
          {!all && pages > 1 && (
            <div className="flex items-center justify-center gap-1 mt-3" aria-label="Pages">
              {Array.from({ length: Math.min(pages, 8) }, (_, i) => <button key={i} aria-current={i === page} onClick={() => setPage(i)} className={`w-7 h-7 rounded-md text-[12px] ${i === page ? "bg-[#2563eb] text-white" : "hover:bg-[#f1f5f9] text-[#475569]"}`}>{i + 1}</button>)}
              {pages > 8 && <span className="text-[#94a3b8] px-1">… {pages}</span>}
            </div>
          )}
          {eff.recipients?.length > 0 && <p className="text-[12px] text-[#64748b] mt-3">Recipients ({eff.recipients.length}): {eff.recipients.slice(0, 6).join(", ")}{eff.recipients.length > 6 ? " …" : ""}</p>}
          {eff.label_path?.length > 0 && <p className="text-[12px] text-[#64748b] mt-1">Data path: {eff.label_path.join(" → ")}</p>}
        </>
      )}
    </Overlay>
  );
}
