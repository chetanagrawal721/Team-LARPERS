import { useMemo, useState } from "react";

// Everything an agent run sent to the language model and got back, grouped per run.
export function groupRuns(events) {
  const runs = new Map();
  for (const e of events) {
    if (e.type !== "agent") continue;
    const id = e.data.run;
    if (!runs.has(id)) runs.set(id, { id, ts: e.ts, request: "", system: "", tools: "", roster: "", attachment: "", agents: {}, turns: [], notices: [] });
    const r = runs.get(id);
    const k = e.data.kind, d = e.data.data || {};
    if (k === "start") Object.assign(r, { request: e.data.text.replace(/^New request: /, ""), system: d.system_prompt || "", tools: d.tools || "", roster: d.roster || "", attachment: d.attachment || "", agents: d.agents || {} });
    else if (k === "llm_request") r.turns.push({ turn: d.turn, messages: d.messages || [], reply: null, provider: "" });
    else if (k === "llm_response" && r.turns.length) { const t = r.turns[r.turns.length - 1]; t.reply = d.raw; t.provider = `${d.provider} · ${d.model}`; }
    else if (k === "llm_notice") r.notices.push(e.data.text);
  }
  return [...runs.values()].reverse();
}

// The exact text of one model call, role by role, as the model received it.
const wholeText = (msgs) => msgs.map((m) => `===== ${m.role.toUpperCase()} =====\n${m.content}`).join("\n\n");

const ROLE = { system: "bg-[#f5f3ff] text-[#6d28d9]", user: "bg-[#eff6ff] text-[#1d4ed8]", assistant: "bg-[#f0fdf4] text-[#15803d]" };

function Copy({ text }) {
  const [ok, setOk] = useState(false);
  return <button className="btn btn-quiet !py-0.5 !px-2 text-[12px]" onClick={() => { navigator.clipboard?.writeText(text); setOk(true); setTimeout(() => setOk(false), 1500); }}>{ok ? "Copied" : "Copy"}</button>;
}

const Block = ({ title, text, open = false, tone = "bg-[#f8fafc] border-[#e3e8ef]" }) => (
  <details open={open} className="card p-3.5">
    <summary className="cursor-pointer text-[13px] font-semibold flex items-center justify-between">{title}<span onClick={(e) => e.stopPropagation()}><Copy text={text} /></span></summary>
    <pre className={`mt-2 text-[12px] leading-5 whitespace-pre-wrap border rounded-lg p-3 max-h-[320px] overflow-auto ${tone}`}>{text || "(empty)"}</pre>
  </details>
);

export default function PromptsView({ events }) {
  const runs = useMemo(() => groupRuns(events), [events]);
  const [sel, setSel] = useState(null);
  const [whole, setWhole] = useState(false);
  const run = runs.find((r) => r.id === sel) || runs[0];
  if (!run) return <div className="flex-1 px-5 py-4 text-[13px] text-[#64748b]">No agent run yet. After you send a request, this tab shows the complete system prompt, each agent's own prompt, the tools, the attached document, every message sent to the language model and every raw reply.</div>;
  const last = run.turns[run.turns.length - 1];
  return (
    <div className="flex-1 overflow-auto px-5 py-4 space-y-3">
      <div className="flex items-center gap-2">
        <select className="field !py-1.5 flex-1" value={run.id} onChange={(e) => setSel(e.target.value)} aria-label="Agent run">
          {runs.map((r) => <option key={r.id} value={r.id}>{new Date(r.ts * 1000).toLocaleTimeString()} · {r.request.slice(0, 60)}</option>)}
        </select>
        <label className="flex items-center gap-1.5 text-[12px] text-[#475569] whitespace-nowrap"><input type="checkbox" checked={whole} onChange={(e) => setWhole(e.target.checked)} />Show whole prompt</label>
      </div>
      {run.notices.length > 0 && <div className="rounded-lg border border-[#fde68a] bg-[#fffbeb] px-3 py-2 text-[12px] text-[#92400e]">Model service notes: {run.notices.join(" · ")}</div>}

      {whole ? (
        <>
          <p className="text-[12px] text-[#64748b]">The exact text of each call to the language model, in order, exactly as the model received it (system prompt, then the conversation).</p>
          {run.turns.map((t, i) => (
            <div key={i} className="card p-3.5 space-y-2">
              <div className="flex items-center justify-between"><b className="text-[13px]">Call {t.turn}{t.provider ? ` · ${t.provider}` : ""}</b><Copy text={wholeText(t.messages)} /></div>
              <pre className="text-[12px] leading-5 whitespace-pre-wrap bg-[#f8fafc] border border-[#e3e8ef] rounded-lg p-3 max-h-[420px] overflow-auto">{wholeText(t.messages)}</pre>
              <div className="text-[12px] text-[#64748b]">The model answered:</div>
              <pre className="text-[12px] leading-5 whitespace-pre-wrap bg-[#f0fdf4] border border-[#bbf7d0] rounded-lg p-3 max-h-[240px] overflow-auto">{t.reply ?? "(no reply received)"}</pre>
            </div>
          ))}
        </>
      ) : (
        <>
          <Block title="System prompt (sent with every call)" text={run.system} open />
          {run.attachment && <Block title="Attached document (pasted with the request)" text={run.attachment} tone="bg-[#fffbeb] border-[#fde68a]" />}
          <Block title="Agents and their own prompts" text={Object.entries(run.agents).map(([id, p]) => `### ${id}\n${p}`).join("\n\n")} />
          <Block title="Tools" text={run.tools} />
          {run.turns.map((t, i) => (
            <div key={i} className="card p-3.5 space-y-2">
              <div className="text-[13px] font-semibold">Call {t.turn}{t.provider ? ` · ${t.provider}` : ""}</div>
              <details open={t === last}>
                <summary className="cursor-pointer text-[12px] text-[#64748b]">Sent to the model ({t.messages.length} messages)</summary>
                <div className="mt-2 space-y-1.5">
                  {t.messages.map((m, j) => (
                    <div key={j} className="rounded-lg border border-[#e3e8ef]">
                      <div className={`px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide rounded-t-lg ${ROLE[m.role] || "bg-[#f1f5f9]"}`}>{m.role}</div>
                      <pre className="px-2.5 py-2 text-[12px] leading-5 whitespace-pre-wrap max-h-[200px] overflow-auto">{m.role === "system" ? "(the system prompt above)" : m.content}</pre>
                    </div>
                  ))}
                </div>
              </details>
              <div className="text-[12px] text-[#64748b]">Model replied (raw)</div>
              <pre className="text-[12px] leading-5 whitespace-pre-wrap bg-[#f0fdf4] border border-[#bbf7d0] rounded-lg p-3 max-h-[200px] overflow-auto">{t.reply ?? "(no reply received)"}</pre>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
