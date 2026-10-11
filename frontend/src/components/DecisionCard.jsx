import { useState } from "react";
import ThreeStageStrip from "./ThreeStageStrip";
import { STATUS_TEXT, USERS, call, getUser, headline, scopeSentence, setUser, tidy } from "../api";

const TONE = {
  ALLOW: ["#1a7f37", "Allowed"], HOLD: ["#9a6700", "Needs approval"], BLOCK: ["#cf222e", "Blocked"], VOID: ["#cf222e", "Voided"], DONE: ["#1a7f37", "Done"],
};

function Stepper({ d }) {
  const needed = Math.max(d.approvals_needed, 1);
  const steps = [
    { label: "Requested", on: true },
    { label: `Approved ${Math.min(d.approvals.length, needed)} of ${needed}`, on: d.approvals.length >= needed, now: d.status === "pending" },
    { label: "Sealed", on: ["approved", "done"].includes(d.status) || d.status === "void", now: d.status === "approved" },
    { label: d.status === "void" ? "Voided" : "Executed", on: ["done", "void"].includes(d.status), bad: d.status === "void" },
  ];
  return (
    <ol className="flex items-center gap-2 text-[12px]" aria-label="Progress">
      {steps.map((s, i) => (
        <li key={s.label} className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${s.bad ? "bg-[#cf222e]" : s.on ? "bg-[#1a7f37]" : s.now ? "bg-[#9a6700]" : "bg-[#d0d7de]"}`} />
          <span className={s.on || s.now ? "text-[#1f2328]" : "text-[#59636e]"}>{s.label}</span>
          {i < steps.length - 1 && <span className="w-5 h-px bg-[#d0d7de]" />}
        </li>
      ))}
    </ol>
  );
}

export default function DecisionCard({ d, onOpenDiff, onOpenShadow, onChanged, notify, onUser }) {
  const [busy, setBusy] = useState("");
  const [user, setUserState] = useState(getUser().name);
  const act = async (label, fn) => {
    setBusy(label);
    try { const out = await fn(); onChanged && onChanged(out); }
    catch (e) { notify && notify("error", `${label}: ${e.message}`); }
    finally { setBusy(""); }
  };
  const shown = d.status === "void" ? "VOID" : d.verdict;
  const [color, word] = TONE[shown] || TONE.HOLD;
  const canApprove = d.verdict === "HOLD" && d.status === "pending";
  const sealed = d.status === "approved";
  const pickUser = (u) => { setUser(u); setUserState(u); onUser && onUser(u); };
  const showSteps = d.verdict === "HOLD" || ["approved", "done", "void"].includes(d.status) && d.approvals.length > 0;
  const trimmed = tidy((d.reason || "").replace(/\s*\|\s*replaced by safe version.*/, ""));

  return (
    <article className="space-y-3">
      <header>
        <h2 className="text-[17px] font-semibold leading-snug">{headline(d)}</h2>
        <p className="text-[13px] text-[#59636e] mt-0.5">
          {scopeSentence(d)} {d.agent_claim && <>The agent said: “{d.agent_claim}”.</>}
        </p>
      </header>

      <div className="panel flex items-center justify-between gap-4 px-4 py-2.5" style={{ borderLeft: `3px solid ${color}` }}>
        <div className="min-w-0">
          <div className="font-semibold" style={{ color }}>{word} <span className="font-normal text-[#59636e]">· rule {d.rule}{d.tier ? ` · tier ${d.tier}` : ""}</span></div>
          <div className="text-[13px] text-[#3d444d]">{trimmed}</div>
        </div>
        <div className="text-[12px] text-[#59636e] text-right shrink-0">
          A request-level gate would have said<br /><b className={d.baseline_verdict === "ALLOW" && shown !== "ALLOW" ? "text-[#9a6700]" : "text-[#3d444d]"}>{d.baseline_verdict}</b>
        </div>
      </div>

      <ThreeStageStrip d={d} />

      {d.safe_version && ["blocked", "pending"].includes(d.status) && (
        <div className="panel px-4 py-2.5 text-[13px]">
          <span className="label mr-2">Smallest safe version</span>
          {d.safe_version.description}. It would be {d.safe_version.verdict === "ALLOW" ? "allowed" : "held for approval"} on its own.
        </div>
      )}

      {showSteps && <Stepper d={d} />}
      {d.status === "shadow" && !d.shadow_session && null}

      <div className="flex flex-wrap items-center gap-2 pt-1">
        {d.safe_version && ["blocked", "pending"].includes(d.status) &&
          <button className="btn btn-primary" disabled={!!busy} onClick={() => act("Safe version", () => call(`/safe-version/${d.id}`, { method: "POST", auth: true }))}>Apply smallest safe version</button>}
        {canApprove && <button className="btn btn-primary" disabled={!!busy} onClick={() => act("Approve", () => call("/approve", { method: "POST", body: { decision_id: d.id }, auth: true }))}>Approve</button>}
        {canApprove && <button className="btn" disabled={!!busy} onClick={() => act("Reject", () => call("/reject", { method: "POST", body: { decision_id: d.id }, auth: true }))}>Reject</button>}
        {sealed && <button className="btn btn-primary" disabled={!!busy} onClick={() => act("Execute", () => call(`/execute/${d.id}`, { method: "POST", auth: true }))}>Execute sealed action</button>}
        {d.action === "transfer" && sealed && <button className="btn" disabled={!!busy} onClick={() => act("Insert invoices", async () => { const r = await call("/demo/insert-invoices", { method: "POST" }); notify("ok", `${r.inserted.toLocaleString("en-IN")} matching invoices were added to the database.`); return r; })}>Add 3,960 matching invoices</button>}
        {d.shadow_session && <button className="btn" onClick={() => onOpenShadow(d.shadow_session)}>Review sandbox work</button>}
        <button className="btn btn-quiet" onClick={() => onOpenDiff(d)}>View changes</button>
        {(canApprove || sealed || d.safe_version) && (
          <label className="ml-auto flex items-center gap-1.5 text-[12px] text-[#59636e]">Acting as
            <select className="bg-[#ffffff] border border-[#d0d7de] rounded px-1.5 py-1 text-[#1f2328]" value={user} onChange={(e) => pickUser(e.target.value)}>
              {USERS.map((u) => <option key={u.id} value={u.id}>{u.label}</option>)}
            </select>
          </label>
        )}
      </div>

      <details className="text-[12px] text-[#59636e]">
        <summary className="cursor-pointer hover:text-[#3d444d]">Details</summary>
        <dl className="grid grid-cols-[110px_1fr] gap-y-1 mt-2">
          <dt>Decision</dt><dd className="font-mono">{d.id} · {STATUS_TEXT[d.status] || d.status}</dd>
          <dt>Rules fired</dt><dd>{d.rules_fired.join(", ") || "none"}</dd>
          <dt>Decided by</dt><dd>{d.decision_path === "rules+ai" ? "rules, with an AI check that can only escalate" : d.decision_path === "fallback" ? "rules only (AI unavailable or off)" : "rules only"}</dd>
          <dt>Policy version</dt><dd className="font-mono">{d.policy_hash.slice(0, 10)}</dd>
          {d.ai_reason && d.ai_reason !== d.reason && <><dt>Note</dt><dd>{d.ai_reason}</dd></>}
        </dl>
      </details>
    </article>
  );
}
