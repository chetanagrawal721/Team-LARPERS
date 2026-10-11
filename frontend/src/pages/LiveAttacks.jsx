import { useEffect, useMemo, useState } from "react";
import { call, num, rupees } from "../api";

const DOMAIN = { bank: "Bank", hospital: "Hospital", shop: "Shop" };

// Everything shown for a run is derived from what really happened: the model's own reply, the proposal it signed,
// and the decision the gateway stored. Nothing here is a script.
function useOutcome(runId, activity) {
  const evs = useMemo(() => activity.filter((e) => e.type === "agent" && e.data.run === runId), [activity, runId]);
  const call_ = evs.find((e) => e.data.kind === "tool_call");
  const result = evs.find((e) => e.data.kind === "tool_result");
  const thought = evs.find((e) => e.data.kind === "thought");
  const answer = evs.find((e) => e.data.kind === "answer");
  const error = evs.find((e) => e.data.kind === "error");
  const finished = !!(answer || error);
  const decisionId = result?.data?.data?.decision;
  const [d, setD] = useState(null);
  useEffect(() => { if (decisionId) call(`/status/${decisionId}`).then(setD).catch(() => {}); }, [decisionId]);
  return { evs, call_, result, thought, answer, error, finished, d, started: evs.length > 0 };
}

function Step({ n, title, state, children }) {
  const tone = state === "ok" ? "bg-[#16a34a]" : state === "bad" ? "bg-[#dc2626]" : state === "warn" ? "bg-[#d97706]" : "bg-[#cbd5e1]";
  return (
    <li className="flex gap-3">
      <div className="flex flex-col items-center"><span className={`w-6 h-6 rounded-full text-white text-[11px] font-semibold grid place-items-center ${tone}`}>{n}</span><span className="w-px flex-1 bg-[#e3e8ef]" /></div>
      <div className="pb-4 min-w-0 text-[13px]"><div className="font-semibold">{title}</div><div className="text-[#334155]">{children}</div></div>
    </li>
  );
}

function Outcome({ run, activity, a }) {
  const o = useOutcome(run, activity);
  if (!o.started) return <p className="text-[13px] text-[#64748b]">Starting the agent…</p>;
  const d = o.d;
  const rows = d?.effect ? Object.values(d.effect.rows).reduce((x, v) => x + v.length, 0) : 0;
  const outside = d?.envelope_check ? Object.values(d.envelope_check.offending_rows || {}).reduce((x, v) => x + v.length, 0) || d.envelope_check.over_rows : 0;
  const proposed = o.call_ ? o.call_.data.text : null;
  const blocked = d && (d.verdict === "BLOCK" || d.status === "blocked");
  const fooled = !!(d && (outside > 0 || blocked));      // judged by what the sandbox measured, not by whether a tool was called
  return (
    <ol className="mt-1">
      <Step n="1" title="The agent read the request and the document" state={o.thought ? "ok" : "none"}>{o.thought ? `Model's reasoning: “${o.thought.data.text}”` : "Waiting for the language model…"}</Step>
      <Step n="2" title={fooled ? "The agent was fooled" : d ? "The agent was not fooled" : proposed ? "The agent proposed an action" : o.finished ? "The agent did not act" : "What the agent decided"} state={fooled ? "bad" : d ? "ok" : "none"}>
        {proposed ? <>It proposed <code className="text-[12px] bg-[#f1f5f9] rounded px-1 break-all">{proposed}</code>{d ? (fooled ? ", which goes further than the user's request." : ", which matches what the user asked for.") : "."}</>
          : o.finished ? (o.answer ? `It answered without acting: “${o.answer.data.text.slice(0, 240)}”` : `It failed: ${o.error?.data.text}`) : "…"}
      </Step>
      <Step n="3" title="Sandbox run" state={d ? (outside ? "bad" : "ok") : "none"}>
        {d?.effect ? <>The gateway applied the proposal to a <b>copy</b> of the data. It would touch <b>{num(rows)}</b> rows{d.effect.amount_minor ? ` (${rupees(d.effect.amount_minor)})` : ""}{d.effect.recipients?.length ? ` and ${num(d.effect.recipients.length)} recipients` : ""}; <b className={outside ? "text-[#b91c1c]" : ""}>{num(outside)} of them are outside what the user asked for</b>. Real data was not touched.</> : fooled ? "Measuring…" : "—"}
      </Step>
      <Step n="4" title="Gateway verdict" state={d ? (blocked ? "bad" : "warn") : "none"}>
        {d ? <><b className={blocked ? "text-[#b91c1c]" : "text-[#b45309]"}>{d.verdict}</b> by rule <b>{d.rule}</b>: {d.reason.split(" | ")[0]}. A request-level gate would have said <b>{d.baseline_verdict}</b>.</> : "—"}
      </Step>
      <Step n="5" title={fooled ? "What the user gets instead" : "What happens next"} state={d?.safe_version || (d && !fooled) ? "ok" : "none"}>
        {d && !fooled ? "Nothing to correct: the proposal matches the request. A person approves or rejects it on the Live Gate." : d?.safe_version ? <>Smallest safe version: <b>{d.safe_version.description}</b>, which would be {d.safe_version.verdict === "ALLOW" ? "allowed" : "held for approval"} on its own. A person still decides on the Live Gate.</> : d ? "No safe version is offered for this case." : "—"}
      </Step>
      {o.finished && <li className="text-[13px] text-[#475569]">{blocked ? <b className="text-[#15803d]">The agent was fooled, the gateway stopped it. Nothing ran.</b> : d ? <b className="text-[#15803d]">The agent resisted the attack: its proposal matches the request and is held for a person to approve. Nothing ran.</b> : "The agent did not attempt the action. Model behaviour varies between runs; run it again."}</li>}
    </ol>
  );
}

function AttackCard({ a, activity, onRun, run, provider }) {
  const [request, setRequest] = useState(a.request);
  const [attachment, setAttachment] = useState(a.attachment);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const go = async () => { setBusy(true); try { await onRun(a, request, attachment, provider); } finally { setBusy(false); } };
  const o = useOutcome(run, activity);
  const running = !!run && !o.finished;
  return (
    <article className="card p-5 space-y-3">
      <header className="flex items-start justify-between gap-3">
        <div><h2 className="text-[15px] font-semibold">{a.title}</h2><p className="text-[12px] text-[#64748b]">{DOMAIN[a.domain]} · goal of the attack: {a.goal}</p></div>
        <button className="btn btn-primary shrink-0" disabled={busy || running} onClick={go}>{running ? "Running…" : run ? "Execute again" : "Execute"}</button>
      </header>
      <div>
        <div className="h-label mb-1">What the user asks (short and narrow)</div>
        <textarea className="field" rows={2} value={request} onChange={(e) => setRequest(e.target.value)} aria-label="User request" />
      </div>
      <div>
        <button className="text-[12px] text-[#2563eb] underline" onClick={() => setOpen(!open)}>{open ? "Hide" : "Show"} the attached document ({attachment.length.toLocaleString("en-IN")} characters, contains the buried instruction)</button>
        {open && <textarea className="field font-mono !text-[12px] mt-1.5" rows={14} value={attachment} onChange={(e) => setAttachment(e.target.value)} aria-label="Attached document" />}
      </div>
      {run && <div className="border-t border-[#eef1f6] pt-3"><Outcome run={run} activity={activity} a={a} /></div>}
      {!run && <p className="text-[12px] text-[#64748b]">Documented expectation (not a script): {a.expected}</p>}
    </article>
  );
}

export default function LiveAttacks({ activity, onWatch, notify }) {
  const [attacks, setAttacks] = useState([]);
  const [runs, setRuns] = useState({});
  const [mode, setMode] = useState(null);
  const [provider, setProvider] = useState("");
  useEffect(() => { call("/attacks").then(setAttacks).catch(() => {}); call("/agent/mode").then(setMode).catch(() => {}); }, []);
  const execute = async (a, request, attachment, prov) => {
    try {
      const r = await call(`/attacks/${a.id}/run`, { method: "POST", body: { request, attachment, provider: prov } });
      setRuns((m) => ({ ...m, [a.id]: r.run }));
      onWatch();
    } catch (e) { notify("error", `Could not start the agent: ${e.message}`); }
  };
  return (
    <div className="space-y-4">
      <div className="card p-4 text-[13px] text-[#334155]">
        <b>How these work.</b> Each card is a normal-looking request plus a long document (a ticket, a letter, a memo) with an instruction buried inside it. Pressing <b>Execute</b> hands both to the live agent. The language model reads them and may be fooled into asking for more than the user wanted. Whatever it proposes is then measured on a sandbox copy and checked against the user's actual request. Nothing is scripted: if the model is not fooled, you will see that instead.
      </div>
      <label className="flex items-center gap-2 text-[13px] text-[#475569]">Language model for these runs
        <select className="field !w-auto !py-1" value={provider} onChange={(e) => setProvider(e.target.value)} aria-label="Language model">
          <option value="">Default ({mode?.providers?.[0] || "none"})</option>
          {(mode?.providers || []).map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
        <span className="text-[12px] text-[#64748b]">Models differ in how easily they are fooled: try the local one if a hosted model resists.</span>
      </label>
      {attacks.map((a) => <AttackCard key={a.id} a={a} activity={activity} run={runs[a.id]} onRun={execute} provider={provider} />)}
      {attacks.length === 0 && <p className="text-[#64748b]">Loading…</p>}
    </div>
  );
}
