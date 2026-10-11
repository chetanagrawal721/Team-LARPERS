import { useEffect, useState } from "react";
import Overlay from "./Overlay";
import Icon from "./Icon";
import { ACTION_LABEL, AGENT_LABEL, call, getUser, num, plural, rupees } from "../api";

const stepText = (s) => {
  const a = s.args || {};
  if (s.action === "payee_change") return `Changed payee (${a.vendor} → ${String(a.new_account || "").split("-")[0] || "new account"})`;
  if (s.action === "transfer") return `Prepared transfer${a.vendor ? ` (${a.vendor})` : " (all pending invoices)"}`;
  if (s.action === "update_contact") return `Updated contact details (${a.customer})`;
  if (s.action === "send_report") return `Prepared report for ${a.patient}`;
  if (s.action === "send_email") return `Prepared email to list “${a.list}”`;
  return ACTION_LABEL[s.action] || s.action;
};

const NOUN = { payee_change: "payee change", transfer: "transfer", update_contact: "contact update", send_report: "report", send_email: "email", refund: "refund", delete_record: "deletion", grant_role: "role grant", write_file: "file" };

const sourceOf = (v) => {
  const first = v.steps[0]?.args?.source || "";
  if (String(first).startsWith("inbox:")) return "Email from an untrusted domain (inbound inbox message)";
  return v.reason.replace(/^R\d+:\s*/, "").replace("UNTRUSTED", "untrusted");
};

export default function ShadowOverlay({ sid, onClose, notify, onChanged }) {
  const [v, setV] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const load = () => call(`/shadow/${sid}`).then(setV).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, [sid]);
  const act = async (path) => {
    setBusy(true);
    try {
      const out = await call(`/${path}/${sid}`, { method: "POST", auth: true });
      if (out.status === "promoted") notify("ok", "The sandbox work was applied to the real data.");
      else if (out.status === "discarded") notify("ok", "The sandbox work was discarded. Real data is unchanged.");
      else if (out.status === "void") notify("error", `Not applied: the real data changed since the sandbox started (${(out.drift || "").replace("_", " ")}). Nothing was changed.`);
      else notify("ok", `${out.approvals.length} of ${out.needed} approvals recorded. One more person must apply this.`);
      onChanged && onChanged(); await load();
    } catch (e) { notify("error", e.message); } finally { setBusy(false); }
  };
  if (err) return <Overlay title="Shadow mode review" onClose={onClose}><p className="text-[#b91c1c]">{err}</p></Overlay>;
  if (!v) return <Overlay title="Shadow mode review" onClose={onClose}>Loading…</Overlay>;
  const active = v.status === "active";
  const changes = Object.values(v.diff).reduce((n, t) => n + Object.keys(t).length, 0);
  const kinds = {};
  v.steps.forEach((s) => { kinds[s.action] = (kinds[s.action] || 0) + 1; });
  const head = Object.entries(kinds).map(([a, n]) => `${n} ${NOUN[a] || a}${n === 1 ? "" : "s"}`).join(", ");

  return (
    <Overlay title="Shadow mode review" onClose={onClose} width={820}
             badge={<span className="pill pill-shadow mr-1">SHADOW</span>}
             subtitle={`${AGENT_LABEL(v.agent)} · suspicious activity detected (${v.reason.includes("UNTRUSTED") ? "untrusted source" : "held for review"})`}
             footer={active ? (
               <div className="flex flex-wrap items-center gap-2">
                 <button className="btn btn-primary" disabled={busy} onClick={() => act("promote")}>Promote to real as {getUser().name}</button>
                 <button className="btn" disabled={busy} onClick={() => act("discard")}>Discard</button>
                 <span className="text-[12px] text-[#64748b] ml-auto">Approvals to apply: {v.approvals.length} of {v.approvals_needed}. Applying replays the recorded actions in one transaction; the real result must equal the sandbox result.</span>
               </div>
             ) : <div className="text-[13px] text-[#64748b]">This session is {v.status}.</div>}>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="rounded-lg border border-[#e3e8ef] p-4">
          <div className="h-label mb-3">Recorded steps</div>
          <ol className="space-y-3">
            {v.steps.map((s) => (
              <li key={s.seq} className="flex items-start gap-2.5 text-[13px]">
                <span className="w-5 h-5 rounded-full bg-[#2563eb] text-white grid place-items-center shrink-0 mt-0.5"><Icon name="check" size={12} stroke={3} /></span>{stepText(s)}
              </li>
            ))}
          </ol>
        </div>
        <div className="space-y-4">
          <div className="rounded-lg border border-[#e3e8ef] p-4">
            <div className="h-label mb-2">Total sandbox result</div>
            <div className="text-[24px] font-semibold leading-tight">{head || "no actions"}</div>
            {v.totals.amount_minor > 0 && <div className="text-[24px] font-semibold text-[#6d28d9]">{rupees(v.totals.amount_minor)}</div>}
          </div>
          <div className="rounded-lg border border-[#e3e8ef] p-4">
            <div className="h-label mb-1">Source of suspicion</div>
            <div className="text-[13px]">{sourceOf(v)}</div>
          </div>
        </div>
      </div>
      <div className="rounded-lg border border-[#e3e8ef] p-4 mt-4">
        <div className="h-label mb-3">Sandbox vs real</div>
        <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4 text-[13px]">
          <div className="rounded-lg bg-[#f5f3ff] p-3"><div className="text-[11px] text-[#6d28d9] font-semibold">Sandbox</div>{plural(changes, "change")}{v.totals.amount_minor > 0 && ` · ${rupees(v.totals.amount_minor)}`}</div>
          <span className="text-[#94a3b8]">{active ? "≠" : "="}</span>
          <div className="rounded-lg bg-[#f8fafc] p-3"><div className="text-[11px] text-[#64748b] font-semibold">Real</div>{active ? "Untouched" : v.status === "promoted" ? "Updated to match" : "Untouched"}</div>
        </div>
        {Object.entries(v.diff).map(([t, rows]) => <div key={t} className="text-[12px] text-[#64748b] mt-2"><b className="text-[#334155]">{t}</b>: {Object.entries(rows).slice(0, 6).map(([pk, [op]]) => `${op} ${pk}`).join(" · ")}{Object.keys(rows).length > 6 ? " …" : ""}</div>)}
      </div>
    </Overlay>
  );
}
