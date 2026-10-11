import { useEffect, useMemo, useState } from "react";
import Overlay from "../components/Overlay";
import { call, num, rupees } from "../api";
import { useUser } from "../hooks/useUser";

const DOMAIN = { bank: "Bank", hospital: "Hospital", shop: "Shop" };
const CATEGORY = {
  "over-reach": { label: "Over-reach", cls: "bg-[#e0ecff] text-[#1d4ed8] border-[#bcd2ff]", bar: "#2563eb" },
  exfiltration: { label: "Data exfiltration", cls: "bg-[#f3e8ff] text-[#7e22ce] border-[#e9d5ff]", bar: "#9333ea" },
  cascade: { label: "Hidden cascade", cls: "bg-[#ffedd5] text-[#c2410c] border-[#fed7aa]", bar: "#ea580c" },
  "untrusted-source": { label: "Untrusted source", cls: "bg-[#fef3c7] text-[#b45309] border-[#fde68a]", bar: "#d97706" },
  "multi-agent": { label: "Two agents", cls: "bg-[#fee2e2] text-[#b91c1c] border-[#fecaca]", bar: "#dc2626" },
};
const AGENT_NAME = { "refund-agent": "Refund", "ops-agent": "Operations", "records-agent": "Records", "support-agent": "Support", "marketing-agent": "Marketing" };

// Everything shown for a run is derived from what really happened: the model's own reply, the proposals it signed, and the
// decisions the gateway stored. Nothing here is a script.
function useRun(runId, activity) {
  const evs = useMemo(() => activity.filter((e) => (e.type === "agent" || e.type === "sandbox" || e.type === "access") && e.data.run === runId), [activity, runId]);
  const agentEvs = evs.filter((e) => e.type === "agent");
  const steps = [];
  for (const e of agentEvs) {
    if (e.data.kind === "tool_call") steps.push({ call: e, result: null });
    if (e.data.kind === "tool_result" && steps.length) steps[steps.length - 1].result = e;
  }
  const sandboxes = evs.filter((e) => e.type === "sandbox");
  const answer = agentEvs.find((e) => e.data.kind === "answer");
  const error = agentEvs.find((e) => e.data.kind === "error");
  const rejected = agentEvs.filter((e) => e.data.kind === "rejected_call");
  const thoughts = agentEvs.filter((e) => e.data.kind === "thought");
  const accessEvs = evs.filter((e) => e.type === "access");
  const accessPending = accessEvs.length > 0 && accessEvs[accessEvs.length - 1].data.status === "pending";
  return { steps, sandboxes, answer, error, rejected, thoughts, finished: !!(answer || error), started: evs.length > 0, accessPending };
}

function useDecisions(ids, active) {
  const [map, setMap] = useState({});
  const key = ids.join(",");
  useEffect(() => {
    if (!ids.length) return;
    let stop = false;
    const load = () => ids.forEach((id) => call(`/status/${id}`).then((d) => !stop && setMap((m) => ({ ...m, [id]: d }))).catch(() => {}));
    load();
    const t = setInterval(load, 1500);
    return () => { stop = true; clearInterval(t); };
  }, [key, active]);
  return map;
}

export function outcomeOf(run, activity) {
  if (!run) return null;
  const evs = activity.filter((e) => e.type === "agent" && e.data.run === run);
  const res = evs.filter((e) => e.data.kind === "tool_result");
  if (!evs.length) return null;
  if (res.some((e) => e.data.data?.verdict === "BLOCK")) return { label: "Fooled · blocked", tone: "pill-block" };
  if (res.length) return { label: "Resisted · held for a person", tone: "pill-allow" };
  if (evs.some((e) => e.data.kind === "answer" || e.data.kind === "error")) return { label: "Did not act", tone: "pill-neutral" };
  return { label: "Running…", tone: "pill-shadow" };
}

function StepCard({ n, step, d, sandbox, onReplay, notify }) {
  const me = useUser();
  const [busy, setBusy] = useState(false);
  const call_ = step.call.data;
  const rows = d?.effect ? Object.values(d.effect.rows).reduce((x, v) => x + v.length, 0) : 0;
  const outside = d?.envelope_check ? Object.values(d.envelope_check.offending_rows || {}).reduce((x, v) => x + v.length, 0) || d.envelope_check.over_rows : 0;
  const blocked = d && (d.verdict === "BLOCK" || d.status === "blocked");
  const fooled = !!(d && (outside > 0 || blocked));
  const pending = d && d.verdict === "HOLD" && d.status === "pending";
  const approved = d && d.status === "approved";
  const decide = async () => {
    setBusy(true);
    try {
      let cur = d;
      if (pending) cur = await call("/approve", { method: "POST", body: { decision_id: d.id }, auth: true });
      if (cur.status === "approved") { await call(`/execute/${d.id}`, { method: "POST", auth: true }); notify("ok", "Approved by a person and executed on the real data."); }
      else notify("ok", `Approved by ${me}. ${cur.approvals_needed - cur.approvals.length} more approval needed: switch user (top right) and click again.`);
    } catch (e) { notify("error", `${e.message}`); } finally { setBusy(false); }
  };
  return (
    <div className="rounded-xl border border-[#e3e8ef] bg-white overflow-hidden">
      <div className="px-4 py-2.5 bg-[#f8fafc] border-b border-[#e3e8ef] flex items-center justify-between gap-3">
        <div className="text-[13px] font-semibold">Step {n} · {AGENT_NAME[call_.agent] || call_.agent} agent</div>
        {d && <span className={`pill ${blocked ? "pill-block" : d.status === "done" ? "pill-allow" : "pill-hold"}`}>{d.status === "done" ? "EXECUTED" : blocked ? "BLOCKED" : approved ? "APPROVED" : "WAITING FOR A PERSON"}</span>}
      </div>
      <div className="p-4 space-y-2 text-[13px]">
        <div><span className="h-label">It proposed</span><div className="font-mono text-[12px] bg-[#f1f5f9] rounded px-2 py-1 mt-0.5 break-all">{step.call.data.text}</div></div>
        {d ? (
          <>
            <div><span className="h-label">Sandbox</span><div>It would touch <b>{num(rows)}</b> rows{d.effect?.amount_minor ? ` (${rupees(d.effect.amount_minor)})` : ""}{d.effect?.recipients?.length ? ` and ${num(d.effect.recipients.length)} recipients` : ""}; <b className={outside ? "text-[#b91c1c]" : "text-[#15803d]"}>{num(outside)} outside what the user asked for</b>.
              {sandbox && <button className="ml-2 text-[#2563eb] underline text-[12px]" onClick={() => onReplay(sandbox)}>replay animation</button>}</div></div>
            <div><span className="h-label">Gateway</span><div><b className={blocked ? "text-[#b91c1c]" : "text-[#b45309]"}>{d.verdict}</b> by rule <b>{d.rule}</b>: {d.reason.split(" | ")[0]}. A request-level gate would have said <b>{d.baseline_verdict}</b>.</div></div>
            {d.effect?.label_path?.length > 0 && <div className="text-[12px] text-[#64748b]">Data path: {d.effect.label_path.join(" → ")}</div>}
            {fooled && <div className="text-[12px] text-[#15803d]">{d.safe_version ? <>Smallest safe version: <b>{d.safe_version.description}</b>.</> : "No safe version is offered for this case."} Nothing ran.</div>}
            {(pending || approved) && !blocked && (
              <div className="pt-1 flex items-center gap-2 flex-wrap">
                <button className="btn btn-primary" disabled={busy} onClick={decide}>{approved ? "Execute" : "Approve and execute"} as {me}</button>
                <span className="text-[12px] text-[#64748b]">A person decides. If it says you cannot approve, switch user in the top right.</span>
              </div>
            )}
          </>
        ) : <div className="text-[#64748b]">Waiting for the gateway…</div>}
      </div>
    </div>
  );
}

function RunPanel({ run, activity, onReplay, notify }) {
  const r = useRun(run, activity);
  const ids = r.steps.map((s) => s.result?.data?.data?.decision).filter(Boolean);
  const decisions = useDecisions(ids, r.finished);
  if (!r.started) return <p className="text-[13px] text-[#64748b]">Starting the agent…</p>;
  const ds = r.steps.map((s) => decisions[s.result?.data?.data?.decision]);
  const anyBlocked = ds.some((d) => d && (d.verdict === "BLOCK" || d.status === "blocked"));
  const anyHeld = ds.some((d) => d && d.verdict === "HOLD");
  return (
    <div className="space-y-3">
      <div className="text-[13px]">
        {r.accessPending ? <b className="text-[#1d4ed8]">An agent is asking for access. Decide in the window that opened.</b>
          : r.thoughts.length ? <><span className="h-label">The model's reasoning</span><p className="text-[#334155] mt-0.5 line-clamp-4">{r.thoughts[r.thoughts.length - 1].data.text}</p></>
          : <span className="text-[#64748b]">Waiting for the language model…</span>}
      </div>
      {r.rejected.map((e, i) => <div key={i} className="text-[12px] text-[#b45309] bg-[#fffbeb] border border-[#fde68a] rounded-lg px-3 py-2">The model's call was rejected before reaching the gateway: {e.data.text.replace("The call was not sent: ", "")}</div>)}
      {r.steps.map((s, i) => <StepCard key={i} n={i + 1} step={s} d={ds[i]} sandbox={r.sandboxes[i]} onReplay={onReplay} notify={notify} />)}
      {r.finished && (
        <div className={`rounded-lg px-4 py-3 text-[13px] border ${anyBlocked ? "border-[#bbf7d0] bg-[#f6fef9]" : "border-[#e3e8ef] bg-[#f8fafc]"}`}>
          {anyBlocked ? <b className="text-[#15803d]">The agent was fooled, the gateway stopped it. Nothing ran.</b>
            : anyHeld ? <b className="text-[#15803d]">The agent resisted the attack: its proposal matches the request and waits for a person. Nothing ran.</b>
            : r.error ? <b className="text-[#b91c1c]">The run failed: {r.error.data.text}</b>
            : <b>The agent did not attempt the action this time. Models vary between runs; run it again.</b>}
          {r.answer && <div className="mt-1 text-[#475569]">The agent told the user: “{r.answer.data.text.slice(0, 280)}”</div>}
        </div>
      )}
    </div>
  );
}

function AttackModal({ a, run, activity, onRun, onClose, onReplay, notify, mode, provider, setProvider }) {
  const [request, setRequest] = useState(a.request);
  const [attachment, setAttachment] = useState(a.attachment);
  const [busy, setBusy] = useState(false);
  const o = outcomeOf(run, activity);
  const running = !!run && o?.label === "Running…";
  const go = async () => { setBusy(true); try { await onRun(a, request, attachment, provider); } finally { setBusy(false); } };
  const cat = CATEGORY[a.category] || CATEGORY["over-reach"];
  return (
    <Overlay title={a.title} onClose={onClose} width={1040}
             badge={<span className={`chip mr-2 ${cat.cls}`}>{cat.label}</span>}
             subtitle={`${DOMAIN[a.domain]} · goal: ${a.goal}`}
             footer={(
               <div className="flex flex-wrap items-center gap-3">
                 <button className="btn btn-primary" disabled={busy || running} onClick={go}>{running ? "Running…" : run ? "Execute again" : "Execute"}</button>
                 <label className="flex items-center gap-1.5 text-[12px] text-[#64748b]">Language model
                   <select className="field !w-auto !py-1" value={provider} onChange={(e) => setProvider(e.target.value)} aria-label="Language model">
                     <option value="">Default ({mode?.providers?.[0] || "none"})</option>
                     {(mode?.providers || []).map((p) => <option key={p} value={p}>{p}</option>)}
                   </select></label>
                 <span className="text-[12px] text-[#64748b] ml-auto">Pressing Execute grants the agent access. A person still decides on the result.</span>
               </div>
             )}>
      <div className="grid lg:grid-cols-2 gap-5">
        <div className="space-y-3 min-w-0">
          <div>
            <div className="h-label mb-1">What the user asks (short and narrow)</div>
            <textarea className="field" rows={2} value={request} onChange={(e) => setRequest(e.target.value)} aria-label="User request" />
          </div>
          <div>
            <div className="h-label mb-1">Attached document ({attachment.length.toLocaleString("en-IN")} characters, contains the buried instruction)</div>
            <textarea className="field font-mono !text-[12px]" rows={17} value={attachment} onChange={(e) => setAttachment(e.target.value)} aria-label="Attached document" />
          </div>
          <p className="text-[12px] text-[#64748b]">Documented expectation (not a script): {a.expected}</p>
        </div>
        <div className="min-w-0">
          <div className="h-label mb-1">Live run</div>
          {run ? <RunPanel run={run} activity={activity} onReplay={onReplay} notify={notify} /> : <div className="rounded-lg border border-dashed border-[#d5dbe5] p-6 text-center text-[13px] text-[#64748b]">Press <b>Execute</b>. The model reads the request and the document, an agent asks for access, the sandbox runs and the gateway decides. You can watch it here, in the sandbox window and on the Agent activity page.</div>}
        </div>
      </div>
    </Overlay>
  );
}

export default function LiveAttacks({ activity, notify, onReplay }) {
  const [attacks, setAttacks] = useState([]);
  const [runs, setRuns] = useState({});
  const [open, setOpen] = useState(null);
  const [mode, setMode] = useState(null);
  const [provider, setProvider] = useState("");
  const [filter, setFilter] = useState("all");
  useEffect(() => { call("/attacks").then(setAttacks).catch(() => {}); call("/agent/mode").then(setMode).catch(() => {}); }, []);
  const execute = async (a, request, attachment, prov) => {
    try { const r = await call(`/attacks/${a.id}/run`, { method: "POST", body: { request, attachment, provider: prov } }); setRuns((m) => ({ ...m, [a.id]: r.run })); }
    catch (e) { notify("error", `Could not start the agent: ${e.message}`); }
  };
  const cats = ["all", ...new Set(attacks.map((a) => a.category))];
  const shown = attacks.filter((a) => filter === "all" || a.category === filter);
  const results = attacks.map((a) => outcomeOf(runs[a.id], activity)).filter(Boolean);
  const cur = attacks.find((a) => a.id === open);

  return (
    <div className="space-y-4">
      <div className="card p-4 text-[13px] text-[#334155]">
        <b>How these work.</b> Each card is a normal-looking request plus a long document (a ticket, a letter, a memo, an e-mail thread) with an instruction buried inside it. Open a card and press <b>Execute</b>: the live language model reads both and may be fooled into asking for more than the user wanted. Whatever it proposes is replayed in a sandbox window and checked against the user's actual request. Nothing is scripted: if the model is not fooled, you will see that.
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {cats.map((c) => <button key={c} onClick={() => setFilter(c)} className={`chip ${filter === c ? "bg-[#e8f0ff] border-[#bcd2ff] text-[#1d4ed8]" : "border-[#e3e8ef] text-[#475569] hover:bg-[#f8fafc]"}`}>{c === "all" ? "All" : CATEGORY[c]?.label || c}</button>)}
        <span className="ml-auto text-[12px] text-[#64748b]">{results.length} run this session · {results.filter((r) => r.label.startsWith("Fooled")).length} stopped by the gateway</span>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {shown.map((a) => {
          const cat = CATEGORY[a.category] || CATEGORY["over-reach"];
          const o = outcomeOf(runs[a.id], activity);
          return (
            <button key={a.id} onClick={() => setOpen(a.id)} className="card text-left p-0 overflow-hidden hover:shadow-md hover:-translate-y-0.5 transition" aria-label={a.title}>
              <div className="h-1.5" style={{ background: cat.bar }} />
              <div className="p-4 space-y-2.5">
                <div className="flex items-center justify-between gap-2">
                  <span className={`chip ${cat.cls}`}>{cat.label}</span>
                  <span className="text-[11px] text-[#64748b]" title={`Difficulty ${a.difficulty} of 3`}>{"●".repeat(a.difficulty)}<span className="text-[#d0d7de]">{"●".repeat(3 - a.difficulty)}</span></span>
                </div>
                <h3 className="text-[14px] font-semibold leading-snug">{a.title}</h3>
                <p className="text-[12.5px] text-[#64748b]">{a.blurb}</p>
                <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                  <span className="pill pill-neutral">{DOMAIN[a.domain]}</span>
                  {(a.agents || []).map((g, i) => <span key={g} className="flex items-center gap-1">{i > 0 && <span className="text-[#94a3b8]">→</span>}<span className="pill pill-info">{AGENT_NAME[g] || g}</span></span>)}
                </div>
                <div className="flex items-center justify-between pt-1.5 border-t border-[#eef1f6]">
                  {o ? <span className={`pill ${o.tone}`}>{o.label}</span> : <span className="text-[12px] text-[#94a3b8]">Not run yet</span>}
                  <span className="text-[12px] text-[#2563eb] font-medium">Open →</span>
                </div>
              </div>
            </button>
          );
        })}
      </div>
      {attacks.length === 0 && <p className="text-[#64748b]">Loading…</p>}
      {cur && <AttackModal a={cur} run={runs[cur.id]} activity={activity} onRun={execute} onClose={() => setOpen(null)} onReplay={onReplay} notify={notify} mode={mode} provider={provider} setProvider={setProvider} />}
    </div>
  );
}
