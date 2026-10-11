import { useState } from "react";
import Overlay from "./Overlay";
import { rupees } from "../api";

const PAGE = 20;

// Real DB / Sandbox copy / Difference. Rows outside the envelope are red, rows inside are green.
export default function DiffOverlay({ d, onClose }) {
  const [tab, setTab] = useState("diff");
  const [all, setAll] = useState({});
  const eff = d.effect;
  const offending = d.envelope_check?.offending_rows || {};
  const tables = Object.keys(eff?.rows || {});

  return (
    <Overlay title={`Diff · ${d.agent} → ${d.action}`} onClose={onClose} wide>
      <div className="flex gap-2 mb-4">
        {[["real", "Real DB"], ["sandbox", "Sandbox copy"], ["diff", "Difference"]].map(([id, label]) => (
          <button key={id} className={`btn ${tab === id ? "btn-accent" : ""}`} onClick={() => setTab(id)}>{label}</button>
        ))}
      </div>
      {!eff && <p className="text-slate-500">No effect was measured for this decision.</p>}
      {tab === "real" && eff && (
        <p className="text-slate-300">{d.status === "done" ? "The real database now contains the changes below." : "The real database is unchanged — nothing has run."}</p>
      )}
      {tab !== "real" && tables.map((t) => {
        const pks = eff.rows[t];
        const bad = new Set(offending[t] || []);
        const shown = all[t] ? pks : pks.slice(0, PAGE);
        return (
          <div key={t} className="mb-5">
            <div className="text-sm text-slate-400 mb-1">{t} · {pks.length.toLocaleString("en-IN")} changes{bad.size > 0 && <span className="text-rose-300"> · {bad.size} outside the request</span>}</div>
            <table className="w-full text-sm">
              <tbody>
                {shown.map((pk) => {
                  const m = eff.row_meta?.[t]?.[pk] || {};
                  const out = bad.has(pk);
                  return (
                    <tr key={pk} className={out ? "text-rose-300" : "text-emerald-300"}>
                      <td className="pr-3 w-6">{tab === "diff" ? (m.op === "removed" ? "−" : m.op === "modified" ? "~" : "+") : ""}</td>
                      <td className="pr-3 font-mono">{pk}</td>
                      <td className="pr-3 text-slate-400">{m.customer_id || m.patient_id || m.vendor_id || ""}</td>
                      <td className="pr-3 text-slate-400">{m.amount_minor != null ? rupees(m.amount_minor) : ""}</td>
                      <td>{out ? "❌ outside the request" : "✅ inside the request"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {pks.length > PAGE && !all[t] && <button className="btn mt-2" onClick={() => setAll({ ...all, [t]: true })}>show all {pks.length.toLocaleString("en-IN")}</button>}
          </div>
        );
      })}
      {eff?.recipients?.length > 0 && <p className="text-sm text-slate-400">Recipients ({eff.recipients.length}): {eff.recipients.slice(0, 8).join(", ")}{eff.recipients.length > 8 ? " …" : ""}</p>}
      {eff?.label_path?.length > 0 && <p className="text-sm text-slate-400 mt-2">Data path: {eff.label_path.join(" ⟶ ")}</p>}
    </Overlay>
  );
}
