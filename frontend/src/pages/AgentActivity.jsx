import { useEffect, useMemo, useRef, useState } from "react";
import PromptsView from "../components/PromptsView";
import Icon from "../components/Icon";
import { clock, num } from "../api";

const DOT = { ok: "bg-[#16a34a]", denied: "bg-[#dc2626]", warn: "bg-[#d97706]", info: "bg-[#94a3b8]", agent: "bg-[#2563eb]", model: "bg-[#7c3aed]", human: "bg-[#0891b2]" };
const PACE = 650;          // milliseconds between checkpoints while a run is live, so the log can be followed

export function runOf(e) {
  if (e.type === "agent" || e.type === "chat") return e.data.run;
  if (e.type === "pipeline" || e.type === "sandbox") return e.data.run;
  if (e.type === "access") return e.data.run;
  return "";
}

// One checkpoint per event of a run, in the order they happened.
function toEntry(e) {
  const d = e.data;
  if (e.type === "sandbox") return { id: e.id, ts: e.ts, tone: d.outside ? "denied" : "ok", label: "Sandbox", text: `Applied to a copy of the data: ${num(d.total)} rows would change, ${num(d.outside)} of them outside what was asked.`, sandbox: e };
  if (e.type === "pipeline") return { id: e.id, ts: e.ts, tone: d.status === "denied" ? "denied" : d.status === "warn" ? "warn" : d.status === "ok" ? "ok" : "info", label: "Gateway", text: d.text, small: true };
  if (e.type === "access") {
    const who = d.agent_name || d.agent;
    return { id: e.id, ts: e.ts, tone: d.status === "denied" ? "denied" : d.status === "granted" ? "human" : "human", label: "Access", text: d.status === "pending" ? `${who} asked for access to run ${d.tool}.` : `${who} was ${d.status} access by ${d.by}.` };
  }
  const k = d.kind;
  const map = {
    start: ["agent", "Request", d.text.replace(/^New request: /, "")],
    llm_request: ["model", "Language model", `Asked the model (turn ${d.data?.turn})`],
    llm_response: ["model", "Language model", d.text],
    llm_notice: ["warn", "Model service", d.text],
    thought: ["agent", "Thinking", d.text],
    agent_active: ["agent", "Agent", d.text],
    access_wait: ["human", "Access", d.text],
    access_granted: ["human", "Access", d.text],
    access_denied: ["denied", "Access", d.text],
    access_timeout: ["denied", "Access", d.text],
    rejected_call: ["warn", "Checked", d.text],
    tool_call: ["agent", "Proposal", d.text],
    tool_result: [d.data?.verdict === "ALLOW" ? "ok" : d.data?.verdict === "HOLD" ? "warn" : "denied", "Gateway answered", d.text],
    waiting_human: ["human", "Waiting", d.text],
    decision_update: ["human", "Decision", d.text],
    answer: ["agent", "Reply", d.text],
    error: ["denied", "Problem", d.text],
  };
  const m = map[k] || ["info", k, d.text];
  return { id: e.id, ts: e.ts, tone: m[0], label: m[1], text: m[2], detail: k === "llm_response" ? d.data?.raw : k === "tool_call" ? JSON.stringify(d.data?.args, null, 2) : null };
}

function status(evs) {
  const has = (k) => evs.some((e) => e.type === "agent" && e.data.kind === k);
  const lastAccess = [...evs].reverse().find((e) => e.type === "access");
  const res = evs.filter((e) => e.type === "agent" && e.data.kind === "tool_result");
  if (has("error") && !has("answer")) return ["Failed", "pill-block"];
  if (has("answer")) return res.some((e) => e.data.data?.verdict === "BLOCK") ? ["Blocked", "pill-block"] : ["Done", "pill-allow"];
  if (lastAccess && lastAccess.data.status === "pending") return ["Needs your access decision", "pill-info"];
  if (has("waiting_human")) return ["Waiting for a person", "pill-hold"];
  return ["Running", "pill-shadow"];
}

export default function AgentActivity({ activity, onReplay, focusRun }) {
  const runs = useMemo(() => {
    const m = new Map();
    for (const e of activity) {
      const r = runOf(e);
      if (!r) continue;
      if (!m.has(r)) m.set(r, { id: r, ts: e.ts, request: "", evs: [] });
      const run = m.get(r);
      run.evs.push(e);
      if (e.type === "agent" && e.data.kind === "start") run.request = e.data.text.replace(/^New request: /, "");
    }
    return [...m.values()].filter((r) => r.request).reverse();
  }, [activity]);
  const [sel, setSel] = useState(null);
  const [tab, setTab] = useState("trail");
  const run = runs.find((r) => r.id === (sel || focusRun)) || runs[0];
  const entries = useMemo(() => (run ? run.evs.filter((e) => !(e.type === "agent" && e.data.kind === "llm_request" && false)).map(toEntry) : []), [run?.evs.length, run?.id]);
  const [st, stCls] = run ? status(run.evs) : ["", ""];
  const live = run && !["Done", "Blocked", "Failed"].includes(st);

  // Reveal the trail one checkpoint at a time while it is live; finished runs are shown at once.
  const [visible, setVisible] = useState(0);
  const lastRun = useRef(null);
  useEffect(() => { if (run && lastRun.current !== run.id) { lastRun.current = run.id; setVisible(live ? Math.min(1, entries.length) : entries.length); } }, [run?.id]);
  useEffect(() => {
    if (!run) return;
    if (!live) { setVisible(entries.length); return; }
    const id = setInterval(() => setVisible((v) => (v < entries.length ? v + 1 : v)), PACE);
    return () => clearInterval(id);
  }, [run?.id, entries.length, live]);
  const end = useRef(null);
  useEffect(() => { if (live) end.current?.scrollIntoView({ block: "end", behavior: "smooth" }); }, [visible]);

  return (
    <div className="p-6 space-y-4 h-full overflow-auto">
      <div>
        <h1 className="text-[22px] font-semibold">Agent activity</h1>
        <p className="text-[13px] text-[#64748b]">Follow what an agent does, checkpoint by checkpoint: what the model decided, who granted access, every check the gateway ran, and the sandbox result.</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-[minmax(300px,4fr)_8fr] gap-5 items-start">
        <section className="card flex flex-col lg:max-h-[calc(100vh-190px)]" aria-label="Runs">
          <div className="px-4 py-3 font-semibold">Runs</div>
          <ul className="overflow-auto border-t border-[#eef1f6]">
            {runs.map((r) => {
              const [s, c] = status(r.evs);
              return (
                <li key={r.id}>
                  <button onClick={() => { setSel(r.id); setTab("trail"); }} aria-current={run?.id === r.id} className={`w-full text-left px-4 py-3 border-l-[3px] border-b border-b-[#f1f4f8] ${run?.id === r.id ? "bg-[#f3f7ff] border-l-[#2563eb]" : "border-l-transparent hover:bg-[#f8fafc]"}`}>
                    <div className="text-[13px] font-medium line-clamp-2">{r.request}</div>
                    <div className="mt-1 flex items-center gap-2 text-[12px] text-[#64748b]">{clock(r.ts)}<span className={`pill ${c}`}>{s}</span></div>
                  </button>
                </li>
              );
            })}
            {runs.length === 0 && <li className="px-4 py-10 text-center text-[13px] text-[#64748b]">No agent runs yet. Ask an agent something, or execute an attack in the Attack Lab.</li>}
          </ul>
        </section>

        <section className="card p-5 min-h-[420px]" aria-label="Checkpoints">
          {!run ? <p className="text-[#64748b]">Select a run.</p> : (
            <>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0"><h2 className="text-[16px] font-semibold">{run.request}</h2><p className="text-[12px] text-[#64748b]">{run.id} · started {clock(run.ts)}</p></div>
                <span className={`pill ${stCls} shrink-0`}>{st}</span>
              </div>
              <div className="flex gap-6 border-b border-[#e3e8ef] my-3" role="tablist">
                {[["trail", "Checkpoints"], ["prompts", "Prompts"]].map(([id, l]) => <button key={id} role="tab" aria-selected={tab === id} className={`tab ${tab === id ? "tab-active" : ""}`} onClick={() => setTab(id)}>{l}</button>)}
              </div>
              {tab === "prompts" ? <div className="-mx-5"><PromptsView events={run.evs.filter((e) => e.type === "agent")} /></div> : (
                <ol>
                  {entries.slice(0, visible).map((e, i, arr) => (
                    <li key={e.id || i} className="flex gap-3 trail-in">
                      <div className="flex flex-col items-center"><span className={`w-3 h-3 rounded-full mt-1.5 ${DOT[e.tone]}`} />{i < entries.length - 1 && <span className="w-px flex-1 bg-[#e3e8ef]" />}</div>
                      <div className={`flex-1 min-w-0 grid grid-cols-[120px_1fr] gap-3 ${e.small ? "pb-1.5 text-[12.5px]" : "pb-4 text-[13px]"}`}>
                        <div className={`font-medium ${e.small ? "text-[#64748b]" : ""}`}>{e.label}<div className="text-[11px] text-[#94a3b8] font-normal">{new Date(e.ts * 1000).toLocaleTimeString()}</div></div>
                        <div className={e.tone === "denied" ? "text-[#b91c1c]" : "text-[#334155]"}>
                          {e.text}
                          {e.sandbox && <div className="mt-1"><button className="btn !py-0.5 !px-2 text-[12px]" onClick={() => onReplay(e.sandbox)}>Replay the sandbox animation</button></div>}
                          {e.detail && <details className="mt-1"><summary className="cursor-pointer text-[12px] text-[#2563eb]">Show details</summary><pre className="mt-1 text-[12px] whitespace-pre-wrap bg-[#f8fafc] border border-[#e3e8ef] rounded-lg p-2 max-h-[200px] overflow-auto">{e.detail}</pre></details>}
                        </div>
                      </div>
                    </li>
                  ))}
                  {live && visible >= entries.length && <li className="flex gap-3 text-[13px] text-[#64748b]"><Icon name="refresh" size={14} className="animate-spin mt-0.5" />Waiting for the next step…</li>}
                  <div ref={end} />
                </ol>
              )}
            </>
          )}
        </section>
      </div>
    </div>
  );
}
