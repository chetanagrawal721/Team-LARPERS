import { useMemo, useState } from "react";
import Icon from "./Icon";

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
    else if (k === "llm_request") r.turns.push({ turn: d.turn, messages: d.messages || [], reply: null, steps: [] });
    else if (k === "llm_response" && r.turns.length) r.turns[r.turns.length - 1].reply = d.raw;
    r.steps.push(e);
  }
  return [...runs.values()].reverse();
}

const ROLE_STYLE = {
  system: "bg-[#f5f3ff] text-[#6d28d9] border-[#ddd6fe]",
  user: "bg-[#eff6ff] text-[#1d4ed8] border-[#bfdbfe]",
  assistant: "bg-[#f0fdf4] text-[#15803d] border-[#bbf7d0]",
};

function CopyButton({ text, label = "Copy" }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard?.writeText(typeof text === "string" ? text : JSON.stringify(text, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button onClick={copy} className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded border border-[#d5dbe5] bg-white text-[#475569] hover:bg-[#f8fafc]" title="Copy to clipboard">
      <Icon name={copied ? "check" : "audit"} size={12} />
      <span>{copied ? "Copied!" : label}</span>
    </button>
  );
}

export default function PromptsView({ events }) {
  const runs = useMemo(() => groupRuns(events), [events]);
  const [sel, setSel] = useState(null);
  const [expandAll, setExpandAll] = useState(false);
  const [showSystemInTurns, setShowSystemInTurns] = useState(false);

  const run = runs.find((r) => r.id === sel) || runs[0];
  if (!run) {
    return (
      <div className="flex-1 px-5 py-4 text-[13px] text-[#64748b]">
        No agent run yet. When you send a request in Live LLM mode, the full system prompt, the tools, every message sent to the model and every raw reply are captured and inspectable in full detail here.
      </div>
    );
  }

  const exportAll = () => {
    const text = `=== SEALGATE AGENT RUN: ${run.id} ===\nRequest: ${run.request}\nTime: ${new Date(run.ts * 1000).toLocaleString()}\n\n--- SYSTEM PROMPT ---\n${run.system}\n\n--- TOOLS ---\n${run.tools}\n\n` +
      run.turns.map((t) => `--- TURN ${t.turn} ---\nSent to Model:\n${JSON.stringify(t.messages, null, 2)}\n\nModel Reply:\n${t.reply ?? "(no reply)"}\n`).join("\n");
    return text;
  };

  return (
    <div className="flex-1 overflow-auto px-5 py-4 space-y-4">
      {/* Run Selector & Global Controls */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#e3e8ef] pb-3">
        <div className="flex items-center gap-2 flex-1 min-w-[200px]">
          <select className="field !py-1.5 flex-1" value={run.id} onChange={(e) => setSel(e.target.value)} aria-label="Agent run">
            {runs.map((r) => (
              <option key={r.id} value={r.id}>
                {new Date(r.ts * 1000).toLocaleTimeString()} · {r.request.slice(0, 42)} ({r.turns.length} turns)
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setExpandAll((v) => !v)}
            className={`text-[12px] px-2.5 py-1 rounded-md border font-medium ${expandAll ? "bg-[#2563eb] text-white border-[#2563eb]" : "bg-white text-[#475569] border-[#d5dbe5] hover:bg-[#f8fafc]"}`}
            title="Toggle between compact scroll boxes and full expanded view"
          >
            {expandAll ? "✓ Whole Prompts Expanded" : "Show Whole Prompts"}
          </button>
          <CopyButton text={exportAll()} label="Copy All" />
        </div>
      </div>

      {!run.system ? (
        <p className="text-[13px] text-[#64748b]">This run did not use the language model (scripted mode).</p>
      ) : (
        <>
          {/* System Prompt Section */}
          <details open className="card p-3.5">
            <summary className="cursor-pointer text-[13px] font-semibold flex items-center justify-between">
              <span>Full System Prompt (Sent to Model)</span>
              <CopyButton text={run.system} label="Copy Prompt" />
            </summary>
            <pre className={`mt-2 text-[12px] leading-5 whitespace-pre-wrap bg-[#f8fafc] border border-[#e3e8ef] rounded-lg p-3 ${expandAll ? "" : "max-h-[300px]"} overflow-auto font-mono`}>
              {run.system}
            </pre>
          </details>

          {/* Tools Specification Section */}
          <details className="card p-3.5">
            <summary className="cursor-pointer text-[13px] font-semibold flex items-center justify-between">
              <span>Tools Available to Agent ({run.tools.split("\n").filter(Boolean).length})</span>
              <CopyButton text={run.tools} label="Copy Tools" />
            </summary>
            <pre className={`mt-2 text-[12px] leading-5 whitespace-pre-wrap bg-[#f8fafc] border border-[#e3e8ef] rounded-lg p-3 ${expandAll ? "" : "max-h-[220px]"} overflow-auto font-mono`}>
              {run.tools}
            </pre>
          </details>

          {/* Turn by Turn Execution */}
          {run.turns.map((t, i) => (
            <div key={i} className="card p-3.5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="text-[13px] font-semibold flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-[#2563eb] text-white flex items-center justify-center text-[11px] font-bold">{t.turn}</span>
                  <span>Turn {t.turn}</span>
                  <span className="text-[11px] text-[#64748b] font-normal">({t.messages.length} messages in context)</span>
                </div>
                <CopyButton text={JSON.stringify(t.messages, null, 2)} label="Copy Messages" />
              </div>

              {/* Messages Sent to LLM */}
              <details open={expandAll || i === run.turns.length - 1} className="space-y-2">
                <summary className="cursor-pointer text-[12px] text-[#64748b] hover:text-[#1e293b]">
                  Messages Context Sent to LLM
                </summary>
                <div className="mt-2 space-y-2">
                  {t.messages.map((m, j) => {
                    const isSystem = m.role === "system";
                    return (
                      <div key={j} className="rounded-lg border border-[#e3e8ef] bg-white">
                        <div className={`px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide flex items-center justify-between rounded-t-lg border-b ${ROLE_STYLE[m.role] || "bg-[#f1f5f9]"}`}>
                          <span>{m.role}</span>
                          <CopyButton text={m.content} label="Copy" />
                        </div>
                        <div className="px-3 py-2 text-[12px] leading-5">
                          {isSystem && !expandAll && !showSystemInTurns ? (
                            <div className="text-[#64748b] flex items-center justify-between">
                              <span>(System instructions formatted above)</span>
                              <button onClick={() => setShowSystemInTurns(true)} className="text-[#2563eb] underline text-[11px]">Show text here</button>
                            </div>
                          ) : (
                            <pre className={`whitespace-pre-wrap font-mono ${expandAll ? "" : "max-h-[220px]"} overflow-auto`}>
                              {m.content}
                            </pre>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </details>

              {/* Raw Model Reply */}
              <div>
                <div className="flex items-center justify-between text-[12px] text-[#64748b] mb-1">
                  <span className="font-medium text-[#15803d]">Model Reply (Raw Output)</span>
                  <CopyButton text={t.reply ?? ""} label="Copy Reply" />
                </div>
                <pre className={`text-[12px] leading-5 whitespace-pre-wrap bg-[#f0fdf4] border border-[#bbf7d0] rounded-lg p-3 font-mono ${expandAll ? "" : "max-h-[260px]"} overflow-auto`}>
                  {t.reply ?? "(no reply received from language model)"}
                </pre>
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
