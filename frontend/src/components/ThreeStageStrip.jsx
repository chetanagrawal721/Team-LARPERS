import Seal from "./Seal";
import { distinctPeople, num, plural, primary, rowCount, rupees, unitOf } from "../api";

const Col = ({ title, children, tone }) => (
  <div className={`px-4 py-3 min-w-0 ${tone || ""}`}>
    <div className="label mb-1.5">{title}</div>
    {children}
  </div>
);

// Asked for -> Sandbox measured -> Real database. The bar overshoots the dashed limit when the action does more than asked.
export default function ThreeStageStrip({ d }) {
  const eff = d.effect, env = d.envelope, chk = d.envelope_check;
  const { table, rows } = primary(eff);
  const n = rows.length;
  const maxRows = env?.max_rows ?? null;
  const people = distinctPeople(eff);
  const outside = chk && !chk.inside;
  const voided = d.status === "void" || d.verdict === "VOID";
  const done = d.status === "done";
  const sealState = voided ? "cracked" : ["done", "approved", "allowed"].includes(d.status) ? "intact" : "none";
  const drift = (d.reason || "").match(/\((\d[\d,]*) -> (\d[\d,]*) rows\)/);
  const scale = Math.max(n, maxRows ?? 0, 1);
  const limitPct = maxRows != null ? (maxRows / scale) * 100 : null;
  const unit = unitOf(table);

  return (
    <div className="panel grid grid-cols-[1fr_1.25fr_1fr_auto] divide-x divide-[#d0d7de] items-stretch">
      <Col title="Asked for">
        {env ? (
          <ul className="space-y-0.5 text-[13px]">
            {maxRows != null && <li>up to <b>{plural(maxRows, unit)}</b></li>}
            {Object.entries(env.scope || {}).map(([k, v]) => <li key={k} className="text-[#3d444d]">{k} <b>{String(v)}</b></li>)}
            {env.max_amount_minor != null && <li>up to <b>{rupees(env.max_amount_minor)}</b></li>}
            <li className="text-[11px] text-[#59636e] pt-1">{env.source === "ai_from_instruction" ? "read from your request by AI, clamped to policy" : "policy default"}</li>
          </ul>
        ) : <span className="text-[#59636e]">Not evaluated</span>}
      </Col>

      <Col title="Sandbox measured">
        {eff ? (
          <>
            <div className={`text-2xl font-semibold leading-none ${outside ? "text-[#cf222e]" : "text-[#1f2328]"}`}>{num(n)} <span className="text-sm font-normal text-[#59636e]">{unit}{n === 1 ? "" : "s"}</span></div>
            <div className="text-[13px] text-[#3d444d] mt-1">
              {[people > 0 && `${num(people)} ${people === 1 ? "person" : "people"}`, eff.amount_minor > 0 && rupees(eff.amount_minor), eff.recipients?.length > 0 && plural(eff.recipients.length, "recipient")].filter(Boolean).join(" · ") || "no records changed"}
            </div>
            <div className="relative h-1.5 rounded bg-[#eaeef2] mt-2.5" aria-hidden>
              <div className={`absolute inset-y-0 left-0 rounded ${outside ? "bg-[#cf222e]" : "bg-[#1a7f37]"}`} style={{ width: `${Math.max(3, (n / scale) * 100)}%` }} />
              {limitPct != null && <div className="absolute -top-1 -bottom-1 border-l border-dashed border-[#8250df]" style={{ left: `${limitPct}%` }} />}
            </div>
            {limitPct != null && <div className="text-[11px] text-[#59636e] mt-1">dashed line: what was asked for</div>}
            {eff.labels?.length > 0 && <div className="text-[11px] text-[#59636e] mt-1">data: {eff.labels.join(", ")}</div>}
          </>
        ) : <span className="text-[#59636e]">No effect measured</span>}
      </Col>

      <Col title="Real database" tone={voided ? "bg-[#cf222e14]" : ""}>
        {voided ? (
          <div>
            <div className="font-semibold text-[#cf222e]">Seal broken</div>
            <div className="text-[13px]">{(d.drift || "changed").replace("_", " ")}{drift ? `: ${drift[1]} to ${drift[2]} rows` : ""}</div>
            <div className="text-[11px] text-[#59636e] mt-1">nothing was changed</div>
          </div>
        ) : done ? (
          <div><div className="font-semibold text-[#1a7f37]">{num(rowCount(eff))} rows changed</div><div className="text-[11px] text-[#59636e] mt-1">identical to the sandbox result</div></div>
        ) : d.status === "shadow" ? <div className="text-[#9a6700]">Untouched. Work is held in a sandbox.</div>
          : <div className="text-[#59636e]">Untouched</div>}
      </Col>

      <div className="flex items-center px-4"><Seal state={sealState} /></div>
    </div>
  );
}
