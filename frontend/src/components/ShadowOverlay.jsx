import { useEffect, useState } from "react";
import Overlay from "./Overlay";
import { call, getUser, rupees } from "../api";

export default function ShadowOverlay({ sid, onClose, notify }) {
  const [v, setV] = useState(null);
  const [err, setErr] = useState("");
  const load = () => call(`/shadow/${sid}`).then(setV).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, [sid]);
  const act = async (path, label) => {
    try { const out = await call(`/${path}/${sid}`, { method: "POST", auth: true }); notify("ok", `${label}: ${out.status}${out.drift ? " (" + out.drift + ")" : ""}`); await load(); }
    catch (e) { notify("error", `${label} refused: ${e.message}`); }
  };
  if (err) return <Overlay title="Sandbox review" onClose={onClose}><p className="text-[#cf222e]">{err}</p></Overlay>;
  if (!v) return <Overlay title="Sandbox review" onClose={onClose}>loading…</Overlay>;
  const active = v.status === "active";
  return (
    <Overlay title={`Sandbox review · ${v.agent}`} onClose={onClose}>
      <p className="text-[#59636e] text-sm mb-3">Held because: {v.reason}. The agent keeps working in a sandbox · the real data is untouched.</p>
      <div className="flex items-center gap-2 mb-3">
        {v.steps.map((s) => <div key={s.seq} className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-[#9a6700]" title={s.action} />{s.seq < v.steps.length && <span className="w-6 h-0.5 bg-[#d0d7de]" />}</div>)}
        <span className="text-sm text-[#59636e] ml-2">{v.steps.length} recorded action(s)</span>
      </div>
      <ol className="text-sm space-y-1 mb-4">
        {v.steps.map((s) => <li key={s.seq}><b>{s.seq}.</b> {s.action} <span className="text-[#59636e]">{JSON.stringify(s.args)}</span> {s.effect.amount_minor > 0 && <span className="text-[#9a6700]">{rupees(s.effect.amount_minor)}</span>}</li>)}
      </ol>
      <div className="rounded border border-[#d0d7de] p-3 mb-4">
        <div className="text-xs uppercase text-[#59636e] mb-1">Total sandbox diff</div>
        {Object.keys(v.diff).length === 0 && <span className="text-[#59636e]">no changes{!active && " (session closed)"}</span>}
        {Object.entries(v.diff).map(([t, rows]) => (
          <div key={t} className="text-sm"><b>{t}</b>: {Object.entries(rows).slice(0, 6).map(([pk, [op]]) => `${op} ${pk}`).join(" · ")}{Object.keys(rows).length > 6 ? " …" : ""}</div>
        ))}
        {v.totals.amount_minor > 0 && <div className="text-sm text-[#9a6700] mt-1">payments queued in the sandbox: {rupees(v.totals.amount_minor)}</div>}
      </div>
      <div className="text-xs text-[#59636e] mb-3">status: {v.status} · approvals to apply {v.approvals.length}/{v.approvals_needed} {v.approvals.length ? `(${v.approvals.join(", ")})` : ""}</div>
      {active && <div className="flex gap-2">
        <button className="btn" onClick={() => act("discard", "Discard")}>Discard sandbox work</button>
        <button className="btn btn-primary" onClick={() => act("promote", `Promote as ${getUser().name}`)}>Apply to real data</button>
      </div>}
      {active && <p className="text-xs text-[#59636e] mt-2">Applying replays the recorded actions inside one transaction; the real diff must equal the sandbox diff.</p>}
    </Overlay>
  );
}
