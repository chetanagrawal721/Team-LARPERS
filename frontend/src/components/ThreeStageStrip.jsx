import Seal from "./Seal";
import { distinctPeople, primary, rowCount, rupees } from "../api";

// Expected -> Sandbox -> Real. The sandbox bar overshoots the dotted envelope in red when the action does more than asked.
export default function ThreeStageStrip({ d }) {
  const eff = d.effect, env = d.envelope, chk = d.envelope_check;
  const { table, rows } = primary(eff);
  const n = rows.length;
  const maxRows = env?.max_rows ?? null;
  const people = distinctPeople(eff);
  const outside = chk && !chk.inside;
  const scale = Math.max(n, maxRows ?? 0, 1);
  const envPct = maxRows != null ? Math.max(4, (maxRows / scale) * 100) : 100;
  const barPct = Math.max(4, (n / scale) * 100);
  const voided = d.status === "void" || d.verdict === "VOID";
  const done = d.status === "done";
  const sealState = voided ? "cracked" : (done || d.status === "approved" || d.status === "allowed") ? "intact" : "none";
  const drift = (d.reason || "").match(/\((\d[\d,]*) -> (\d[\d,]*) rows\)/);

  return (
    <div className="grid grid-cols-[1fr_1.4fr_1fr_auto] gap-3 items-stretch text-sm">
      <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-3">
        <div className="text-xs uppercase tracking-wide text-slate-400 mb-2">① Expected</div>
        {env ? (
          <ul className="space-y-1">
            {maxRows != null && <li>≤ {maxRows} {table || "rows"}</li>}
            {Object.entries(env.scope || {}).map(([k, v]) => <li key={k}>{k}: <b>{String(v)}</b></li>)}
            {env.max_amount_minor != null && <li>≤ {rupees(env.max_amount_minor)}</li>}
            <li className="text-xs text-slate-500">{env.source === "ai_from_instruction" ? "from your request (AI)" : "policy default"}</li>
          </ul>
        ) : <span className="text-slate-500">—</span>}
      </div>

      <div className={`rounded-lg border p-3 ${outside ? "border-rose-500/60 bg-rose-950/20" : "border-emerald-500/40 bg-emerald-950/10"}`}>
        <div className="text-xs uppercase tracking-wide text-slate-400 mb-2">② Sandbox did</div>
        {eff ? (
          <>
            <ul className="space-y-1 mb-2">
              <li className={outside ? "text-rose-300" : ""}><b>{n.toLocaleString("en-IN")}</b> {table || "rows"} {outside && "⚠"}</li>
              {people > 0 && <li className={outside && people > 1 ? "text-rose-300" : ""}>{people} {people === 1 ? "person" : "people"}</li>}
              {eff.amount_minor > 0 && <li className={chk?.over_amount ? "text-rose-300" : ""}>{rupees(eff.amount_minor)}</li>}
              {eff.recipients?.length > 0 && <li>{eff.recipients.length} recipient(s)</li>}
              {eff.labels?.length > 0 && <li className="text-xs text-slate-400">labels: {eff.labels.join(", ")}</li>}
            </ul>
            <div className="relative h-3 rounded bg-slate-800">
              {maxRows != null && <div className="absolute inset-y-0 left-0 border-r-2 border-dashed border-cyan-300" style={{ width: `${envPct}%` }} />}
              <div className={`absolute inset-y-0 left-0 rounded ${outside ? "bg-rose-500" : "bg-emerald-500"}`} style={{ width: `${barPct}%`, opacity: 0.85 }} />
            </div>
          </>
        ) : <span className="text-slate-500">no effect measured</span>}
      </div>

      <div className={`rounded-lg border p-3 ${voided ? "border-rose-500/60 bg-rose-950/20" : "border-slate-700 bg-slate-900/60"}`}>
        <div className="text-xs uppercase tracking-wide text-slate-400 mb-2">③ Real</div>
        {voided ? (
          <div className="text-rose-300">
            <div className="font-semibold">SEAL BROKEN</div>
            <div className="text-xs">{(d.drift || "drift").replace("_", " ")}{drift ? ` (${drift[1]} → ${drift[2]})` : ""}</div>
            <div className="text-xs text-slate-400 mt-1">nothing ran</div>
          </div>
        ) : done ? (
          <div className="text-emerald-300"><b>{rowCount(eff).toLocaleString("en-IN")}</b> rows changed<div className="text-xs text-slate-400">matches the sandbox</div></div>
        ) : d.status === "shadow" ? <span className="text-amber-300">kept in sandbox</span>
          : <span className="text-slate-500">not run</span>}
      </div>

      <div className="flex items-center"><Seal state={sealState} /></div>
    </div>
  );
}
