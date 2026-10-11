import { useMemo, useState } from "react";

// Everything the agent sent to its language model and everything the model sent back, per run.
export function groupRuns(events) {
  const runs = new Map();
  for (const e of events) {
    if (e.type !== "agent") continue;
    const id = e.data.run;
    if (!runs.has(id)) runs.set(id, { id, ts: e.ts, request: "", system: "", tools: "", turns: [], steps: [] });
    const r = runs.get(id);
    const k = e.data.kind, d = e.data.data || {};
    if (k === "start") { r.request = e.data.text.replace(/^New request: /, ""); r.system = d.system_prompt || ""; r.tools = d.tools || ""; }
    else if (k === "llm_request") r.turns.push({ turn: d.turn, messages: d.messages || [], reply: null });
    else if (k === "llm_response" && r.turns.length) r.turns[r.turns.length - 1].reply = d.raw;
    r.steps.push(e);
  }
  return [...runs.values()].reverse();
}

const ROLE = { system: "bg-[#f5f3ff] text-[#6d28d9]", user: "bg-[#eff6ff] text-[#1d4ed8]", assistant: "bg-[#f0fdf4] text-[#15803d]" };

export default function PromptsView({ events }) {
  const runs = useMemo(() => groupRuns(events), [events]);
  const [sel, setSel] = useState(null);
  const run = runs.find((r) => r.id === sel) || runs[0];
  if (!run) return <div className="flex-1 px-5 py-4 text-[13px] text-[#64748b]">No agent run yet. When you send a request in Live LLM mode, the full system prompt, the tools, every message sent to the model and every raw reply are shown here.</div>;
  return (
    <div className="flex-1 overflow-auto px-5 py-4 space-y-4">
      <div className="flex items-center gap-2">
        <select className="field !py-1.5" value={run.id} onChange={(e) => setSel(e.target.value)} aria-label="Agent run">
          {runs.map((r) => <option key={r.id} value={r.id}>{new Date(r.ts * 1000).toLocaleTimeString()} · {r.request.slice(0, 48)}</option>)}
        </select>
      </div>
      {!run.system ? <p className="text-[13px] text-[#64748b]">This run did not use the language model (scripted).</p> : (
        <>
          <details open className="card p-3.5">
            <summary className="cursor-pointer text-[13px] font-semibold">System prompt (sent with every turn)</summary>
            <pre className="mt-2 text-[12px] leading-5 whitespace-pre-wrap bg-[#f8fafc] border border-[#e3e8ef] rounded-lg p-3 max-h-[300px] overflow-auto">{run.system}</pre>
          </details>
          <details className="card p-3.5">
            <summary className="cursor-pointer text-[13px] font-semibold">Tools this agent may call</summary>
            <pre className="mt-2 text-[12px] leading-5 whitespace-pre-wrap bg-[#f8fafc] border border-[#e3e8ef] rounded-lg p-3">{run.tools}</pre>
          </details>
          {run.turns.map((t, i) => (
            <div key={i} className="card p-3.5 space-y-2">
              <div className="text-[13px] font-semibold">Turn {t.turn}</div>
              <details open={i === run.turns.length - 1}>
                <summary className="cursor-pointer text-[12px] text-[#64748b]">Sent to the model ({t.messages.length} messages)</summary>
                <div className="mt-2 space-y-1.5">
                  {t.messages.map((m, j) => (
                    <div key={j} className="rounded-lg border border-[#e3e8ef]">
                      <div className={`px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide rounded-t-lg ${ROLE[m.role] || "bg-[#f1f5f9]"}`}>{m.role}</div>
                      <pre className="px-2.5 py-2 text-[12px] leading-5 whitespace-pre-wrap max-h-[160px] overflow-auto">{m.role === "system" ? "(the system prompt above)" : m.content}</pre>
                    </div>
                  ))}
                </div>
              </details>
              <div>
                <div className="text-[12px] text-[#64748b] mb-1">Model replied (raw)</div>
                <pre className="text-[12px] leading-5 whitespace-pre-wrap bg-[#f0fdf4] border border-[#bbf7d0] rounded-lg p-3 max-h-[200px] overflow-auto">{t.reply ?? "(no reply received)"}</pre>
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
