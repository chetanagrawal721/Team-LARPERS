import { useState } from "react";
import ThreeStageStrip from "./ThreeStageStrip";
import { VERDICT_COLOR, call, getUser } from "../api";

const Pill = ({ children, className = "" }) => <span className={`px-2 py-0.5 rounded text-xs font-semibold ${className}`}>{children}</span>;
const verdictBg = { ALLOW: "bg-emerald-900/60 text-emerald-300", HOLD: "bg-amber-900/60 text-amber-300", BLOCK: "bg-rose-900/60 text-rose-300", VOID: "bg-rose-900/60 text-rose-300", DONE: "bg-emerald-900/60 text-emerald-300" };

// One component for every decision: only the data changes.
export default function DecisionCard({ d, onOpenDiff, onOpenShadow, onChanged, notify }) {
  const [busy, setBusy] = useState("");
  const act = async (label, fn) => {
    setBusy(label);
    try { const out = await fn(); onChanged && onChanged(out); notify && notify("ok", `${label}: ${out?.status || out?.verdict || "ok"}`); }
    catch (e) { notify && notify("error", `${label} refused: ${e.message}`); }
    finally { setBusy(""); }
  };
  const sealed = d.status === "approved";
  const shown = d.status === "void" ? "VOID" : d.verdict;
  const canApprove = d.verdict === "HOLD" && d.status === "pending";

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900/80 p-4 space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="text-slate-300"><b>{d.agent}</b> → <span className="text-cyan-300">{d.action}</span></div>
          {d.agent_claim && <div className="text-xs text-slate-500">agent's claim: “{d.agent_claim}”</div>}
        </div>
        <div className="flex gap-1 items-center"><Pill className="bg-slate-800 text-slate-300">{d.id}</Pill>{d.tier && <Pill className="bg-slate-800 text-slate-300">{d.tier}</Pill>}</div>
      </div>

      <ThreeStageStrip d={d} />

      <div className="flex flex-wrap items-center gap-3 text-sm">
        <span>Normal gate: <b className={VERDICT_COLOR[d.baseline_verdict]}>{d.baseline_verdict === "ALLOW" ? "🟢" : d.baseline_verdict === "HOLD" ? "🟡" : "🔴"} {d.baseline_verdict}</b></span>
        <span>SEALGATE: <Pill className={verdictBg[shown]}>{shown} · {d.rule}</Pill></span>
        <span className="text-xs text-slate-500">path: {d.decision_path} · policy {d.policy_hash.slice(0, 6)}</span>
      </div>

      <div className="text-sm"><span className="text-slate-400">WHY</span> {d.reason}</div>
      {d.ai_reason && d.ai_reason !== d.reason && <div className="text-xs text-slate-400">{d.ai_reason}</div>}
      {d.safe_version && (
        <div className="rounded-lg border border-cyan-500/40 bg-cyan-950/20 p-2 text-sm">
          <span className="text-cyan-300 font-semibold">Smallest safe version:</span> {d.safe_version.description}
          <span className="text-slate-400"> → {d.safe_version.verdict}</span>
        </div>
      )}
      {d.approvals?.length > 0 && <div className="text-xs text-slate-400">approvals: {d.approvals.join(", ")} (need {d.approvals_needed})</div>}

      <div className="flex flex-wrap gap-2 pt-1">
        <button className="btn" onClick={() => onOpenDiff(d)}>View diff</button>
        {d.safe_version && ["blocked", "pending"].includes(d.status) &&
          <button className="btn btn-accent" disabled={!!busy} onClick={() => act("Safe version", () => call(`/safe-version/${d.id}`, { method: "POST", auth: true }))}>Smallest safe version</button>}
        {canApprove && <button className="btn btn-accent" disabled={!!busy} onClick={() => act("Approve", () => call("/approve", { method: "POST", body: { decision_id: d.id }, auth: true }))}>Approve as {getUser().name}</button>}
        {canApprove && <button className="btn" disabled={!!busy} onClick={() => act("Reject", () => call("/reject", { method: "POST", body: { decision_id: d.id }, auth: true }))}>Reject</button>}
        {sealed && <button className="btn btn-accent" disabled={!!busy} onClick={() => act("Execute", () => call(`/execute/${d.id}`, { method: "POST", auth: true }))}>Execute sealed action</button>}
        {d.action === "transfer" && sealed && <button className="btn" onClick={() => act("Insert invoices", () => call("/demo/insert-invoices", { method: "POST" }))}>Insert invoices (change the data)</button>}
        {d.shadow_session && <button className="btn" onClick={() => onOpenShadow(d.shadow_session)}>Shadow mode</button>}
      </div>
    </div>
  );
}
