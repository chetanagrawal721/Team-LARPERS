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
  if (err) return <Overlay title="Shadow Mode" onClose={onClose}><p className="text-rose-300">{err}</p></Overlay>;
  if (!v) return <Overlay title="Shadow Mode" onClose={onClose}>loading…</Overlay>;
  const active = v.status === "active";
  return (
    <Overlay title={`SHADOW MODE · ${v.agent}`} onClose={onClose}>
      <p className="text-slate-400 text-sm mb-3">Held because: {v.reason}. The agent keeps working in a sandbox · the real data is untouched.</p>
      <div className="flex items-center gap-2 mb-3">
        {v.steps.map((s) => <div key={s.seq} className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-amber-400" title={s.action} />{s.seq < v.steps.length && <span className="w-6 h-0.5 bg-slate-600" />}</div>)}
        <span className="text-sm text-slate-400 ml-2">{v.steps.length} recorded action(s)</span>
      </div>
      <ol className="text-sm space-y-1 mb-4">
        {v.steps.map((s) => <li key={s.seq}><b>{s.seq}.</b> {s.action} <span className="text-slate-500">{JSON.stringify(s.args)}</span> {s.effect.amount_minor > 0 && <span className="text-amber-300">{rupees(s.effect.amount_minor)}</span>}</li>)}
      </ol>
      <div className="rounded border border-slate-700 p-3 mb-4">
        <div className="text-xs uppercase text-slate-400 mb-1">Total sandbox diff</div>
        {Object.keys(v.diff).length === 0 && <span className="text-slate-500">no changes{!active && " (session closed)"}</span>}
        {Object.entries(v.diff).map(([t, rows]) => (
          <div key={t} className="text-sm"><b>{t}</b>: {Object.entries(rows).slice(0, 6).map(([pk, [op]]) => `${op} ${pk}`).join(" · ")}{Object.keys(rows).length > 6 ? " …" : ""}</div>
        ))}
        {v.totals.amount_minor > 0 && <div className="text-sm text-amber-300 mt-1">payments queued in the sandbox: {rupees(v.totals.amount_minor)}</div>}
      </div>
      <div className="text-xs text-slate-500 mb-3">status: {v.status} · promotion approvals {v.approvals.length}/{v.approvals_needed} {v.approvals.length ? `(${v.approvals.join(", ")})` : ""}</div>
      {active && <div className="flex gap-2">
        <button className="btn" onClick={() => act("discard", "Discard")}>Discard</button>
        <button className="btn btn-accent" onClick={() => act("promote", `Promote as ${getUser().name}`)}>Promote to real ▶</button>
      </div>}
      {active && <p className="text-xs text-slate-500 mt-2">Promote replays the recorded actions inside one transaction; the real diff must equal the sandbox diff.</p>}
    </Overlay>
  );
}
