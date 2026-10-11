import { useEffect, useState } from "react";
import Overlay from "./Overlay";
import Icon from "./Icon";
import { ACTION_LABEL, AGENT_LABEL, PILL, ROLE_LABEL, USERS, call, distinctPeople, eligibleApprovers, getUser, setUser, num, pathLabel, plural, primary, rupees, stateOf, unitOf } from "../api";
import { explainOf } from "./ActionDetail";

const DEST = { payment_rail: "Payment rail (money leaves the bank)", external_email: "External email address", internal_email: "Internal email address",
  shared_drive: "Shared drive", rbi_reporting: "Regulatory reporting" };
const LABEL_CLS = { PII: "bg-[#fee2e2] text-[#b91c1c] border-[#fecaca]", SECRET: "bg-[#fee2e2] text-[#7f1d1d] border-[#fca5a5]", INTERNAL: "bg-[#e0ecff] text-[#1d4ed8] border-[#bcd2ff]",
  UNTRUSTED: "bg-[#fef3c7] text-[#b45309] border-[#fde68a]", PUBLIC: "bg-[#f1f5f9] text-[#475569] border-[#e2e8f0]" };
const REV = { none: ["Irreversible", "This cannot be undone once it runs."], compensating: ["Compensating", "A mistake can be corrected only with a reversing entry."], snapshot: null };

const mmss = (s) => `${Math.max(0, Math.floor(s / 60))}:${String(Math.max(0, s % 60)).padStart(2, "0")}`;

export default function ApprovalSheet({ id, onClose, onChanged, onDiff, notify }) {
  const [s, setS] = useState(null);
  const [err, setErr] = useState("");
  const [now, setNow] = useState(Math.floor(Date.now() / 1000));
  const [busy, setBusy] = useState(false);
  const [who, setWho] = useState(getUser().name);
  const load = () => call(`/sheet/${id}`).then(setS).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, [id]);
  useEffect(() => { const t = setInterval(() => setNow(Math.floor(Date.now() / 1000)), 1000); return () => clearInterval(t); }, []);
  if (err) return <Overlay title="Approval sheet" onClose={onClose}><p className="text-[#b91c1c]">{err}</p></Overlay>;
  if (!s) return <Overlay title="Approval sheet" onClose={onClose}>Loading…</Overlay>;

  const d = s.decision, e = d.effect, me = who, meInfo = USERS.find((u) => u.id === me);
  const { table, rows } = primary(e);
  const people = distinctPeople(e);
  const v = stateOf(d);
  const pending = d.verdict === "HOLD" && d.status === "pending";
  const isRequester = me === s.requester;
  const elig = eligibleApprovers(s.requester, d.approvals).map((u) => u.name.split(" ")[0]).join(", ");
  const why = !pending ? (d.status === "approved" ? "Already approved and sealed. Use Execute on the Live Gate." : d.verdict === "BLOCK" ? "Blocked actions cannot be approved; a person can mark them as reviewed on the Live Gate." : `Status: ${d.status}.`)
    : isRequester ? `${meInfo.name} is the requester and cannot approve their own request. Switch to ${elig || "another person"}.`
    : !meInfo?.can ? `${meInfo?.name} cannot approve. Switch to ${elig || "another person"}.` : d.approvals.includes(me) ? `${meInfo.name} has already approved this.` : "";
  const run = async (label, fn) => {
    setBusy(true);
    try { const out = await fn(); onChanged && onChanged(out); await load(); if (label !== "Approve" || out.status === "approved") onClose(); }
    catch (er) { notify("error", `${label}: ${er.message}`); } finally { setBusy(false); }
  };
  const remain = s.expires_ts - now;
  const rev = REV[e?.reversible];

  return (
    <Overlay title={pending ? "You are approving this exact effect" : "Review this action"} onClose={onClose} width={680}
             subtitle={`${AGENT_LABEL(d.agent)} → ${d.action}${s.instruction ? ` · “${s.instruction}”` : ""}`}
             footer={(
               <div className="space-y-3">
                 <div className="flex flex-wrap gap-2">
                   <button className="btn btn-primary" disabled={busy || !!why} onClick={() => run("Approve", () => call("/approve", { method: "POST", body: { decision_id: d.id }, auth: true }))}><Icon name="check" size={15} />Approve this effect</button>
                   <button className="btn btn-danger" disabled={busy || !pending || isRequester} onClick={() => run("Reject", () => call("/reject", { method: "POST", body: { decision_id: d.id }, auth: true }))}>Reject</button>
                   <label className="ml-auto flex items-center gap-1.5 text-[12px] text-[#64748b]">Acting as
                     <select className="field !w-auto !py-1" value={who} onChange={(ev) => { setUser(ev.target.value); setWho(ev.target.value); }} aria-label="Acting as">
                       {USERS.map((u) => <option key={u.id} value={u.id}>{u.name} · {u.role}</option>)}
                     </select></label>
                   <button className="btn btn-quiet" onClick={onClose}>Cancel</button>
                 </div>
                 <div className="text-[12px] text-[#64748b] flex flex-wrap gap-x-3">
                   {pending && <span>Expires in <b className="text-[#0f172a]">{mmss(remain)}</b></span>}
                   <span>{d.approvals.length} of {Math.max(d.approvals_needed, 1)} approvers</span>
                   {why && <span className="text-[#b45309]">{why}</span>}
                 </div>
               </div>
             )}>
      <div className="space-y-4">
        <div className="grid grid-cols-3 gap-3">
          {[["Agent", AGENT_LABEL(d.agent), "agents"], ["Requested by", `${s.requester_name}${s.requester_role ? ` (${ROLE_LABEL(s.requester_role)})` : ""}`, "agents"], ["Action", ACTION_LABEL[d.action] || d.action, "live"]].map(([k, val, ic]) => (
            <div key={k} className="rounded-lg border border-[#e3e8ef] p-3 flex items-center gap-2.5 min-w-0">
              <span className="w-8 h-8 rounded-full bg-[#eef2f8] text-[#475569] grid place-items-center shrink-0"><Icon name={ic} size={15} /></span>
              <div className="min-w-0"><div className="text-[11px] text-[#64748b]">{k}</div><div className="text-[13px] font-semibold truncate">{val}</div></div>
            </div>
          ))}
        </div>

        {e && (
          <div className="rounded-lg border border-[#e3e8ef] p-4">
            <div className="h-label mb-2">Measured effect (sandbox)</div>
            <div className="flex flex-wrap gap-x-10 gap-y-2">
              <div><div className="text-[30px] font-semibold leading-none text-[#b91c1c]">{num(rows.length)}</div><div className="text-[12px] text-[#64748b]">{unitOf(table)}s</div></div>
              {people > 0 && <div><div className="text-[30px] font-semibold leading-none">{num(people)}</div><div className="text-[12px] text-[#64748b]">{people === 1 ? "person" : "people"}</div></div>}
              {e.amount_minor > 0 && <div><div className="text-[30px] font-semibold leading-none text-[#b91c1c]">{rupees(e.amount_minor)}</div><div className="text-[12px] text-[#64748b]">amount</div></div>}
              {e.recipients?.length > 0 && <div><div className="text-[30px] font-semibold leading-none">{num(e.recipients.length)}</div><div className="text-[12px] text-[#64748b]">recipients</div></div>}
            </div>
            <div className="grid grid-cols-2 gap-4 mt-4 pt-3 border-t border-[#eef1f6]">
              <div><div className="text-[11px] text-[#64748b] mb-1">Destination</div><div className="text-[13px]">{(e.destinations.map((x) => DEST[x] || x).join(", ")) || "Internal records only"}</div></div>
              <div><div className="text-[11px] text-[#64748b] mb-1">Data labels</div><div className="flex flex-wrap gap-1.5">{e.labels.length ? e.labels.map((l) => <span key={l} className={`chip ${LABEL_CLS[l] || LABEL_CLS.PUBLIC}`}>{l}</span>) : <span className="text-[13px] text-[#64748b]">none</span>}</div></div>
            </div>
            <button className="btn btn-quiet !px-0 mt-2 text-[#2563eb]" onClick={() => onDiff(d)}>View row-level diff</button>
          </div>
        )}

        {rev && <div className="rounded-lg border border-[#fecaca] bg-[#fff5f5] px-4 py-2.5 text-[13px] text-[#b91c1c] flex items-center gap-2"><Icon name="warn" size={16} /><span><b>{rev[0]}:</b> {rev[1]}</span></div>}

        <div className="rounded-lg border border-[#e3e8ef] p-4 space-y-2">
          <div className="flex items-center justify-between"><div className="h-label">Policy decision</div><span className={`pill ${PILL[v]}`}>{v} · {d.rule}</span></div>
          <div className="text-[12px] text-[#64748b]">Normal gate would say: <b>{d.baseline_verdict}</b> · Decided by {pathLabel(d.decision_path)} · Tier {d.tier}</div>
          <p className="text-[13px] text-[#334155]"><b>Explanation:</b> {explainOf(d)}</p>
        </div>

        {d.safe_version && ["blocked", "pending"].includes(d.status) && (
          <div className="rounded-lg border border-[#bcd2ff] bg-[#f3f7ff] p-4 flex items-center gap-3">
            <div className="flex-1"><div className="text-[11px] font-semibold text-[#1d4ed8]">Smallest safe version</div><div className="text-[13px]">{d.safe_version.description}. It would be {d.safe_version.verdict === "ALLOW" ? "allowed" : "held for approval"} on its own.</div></div>
            <button className="btn btn-primary" disabled={busy} onClick={() => run("Safe version", () => call(`/safe-version/${d.id}`, { method: "POST", auth: true }))}>Use safe version</button>
          </div>
        )}
      </div>
    </Overlay>
  );
}
