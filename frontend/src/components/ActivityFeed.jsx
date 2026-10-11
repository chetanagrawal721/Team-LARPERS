import { useEffect, useRef, useState } from "react";
import Icon from "./Icon";
import { rupees } from "../api";

const COLOR = { ok: "bg-[#16a34a]", denied: "bg-[#dc2626]", warn: "bg-[#d97706]", info: "bg-[#94a3b8]", error: "bg-[#dc2626]", agent: "bg-[#2563eb]", model: "bg-[#7c3aed]", human: "bg-[#0891b2]" };
const t = (ts) => new Date((ts || Date.now() / 1000) * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

// The sandbox result, revealed line by line. Every row is judged against what was asked: approved (inside) or denied (outside).
function SandboxBlock({ ev }) {
  const rows = ev.data.rows || [];
  const [shown, setShown] = useState(0);
  useEffect(() => {
    setShown(0);
    const step = Math.max(1, Math.ceil(rows.length / 60));
    const id = setInterval(() => setShown((n) => { if (n >= rows.length) { clearInterval(id); return n; } return Math.min(rows.length, n + step); }), 30);
    return () => clearInterval(id);
  }, [ev.id]);
  const seen = rows.slice(0, shown);
  const ok = seen.filter((r) => r.inside).length;
  const done = shown >= rows.length;
  return (
    <div className="rounded-lg border border-[#e3e8ef] bg-[#fafbfd] overflow-hidden my-1">
      <div className="px-3 py-2 flex items-center justify-between border-b border-[#e3e8ef] bg-white">
        <span className="text-[12px] font-semibold">Sandbox, row by row · {ev.data.agent} → {ev.data.action}</span>
        <span className="text-[12px]"><b className="text-[#15803d]">{ok} approved</b> · <b className="text-[#b91c1c]">{seen.length - ok} denied</b> · {shown}/{ev.data.total}{!done && " …"}</span>
      </div>
      <ul className="max-h-[220px] overflow-auto font-mono text-[11.5px]">
        {seen.map((r, i) => (
          <li key={i} className={`px-3 py-0.5 flex gap-2 ${r.inside ? "text-[#166534]" : "text-[#b91c1c] bg-[#fff5f5]"}`}>
            <span className="w-[62px] shrink-0 font-semibold">{r.inside ? "APPROVED" : "DENIED"}</span>
            <span className="w-[100px] shrink-0 truncate">{r.pk}</span>
            <span className="w-[56px] shrink-0 text-[#64748b]">{r.who}</span>
            <span className="flex-1 truncate">{r.name}</span>
            <span className="shrink-0">{r.amount_minor != null ? rupees(r.amount_minor) : ""}</span>
          </li>
        ))}
        {ev.data.truncated && done && <li className="px-3 py-1 text-[#64748b]">… showing the first {rows.length} of {ev.data.total} rows</li>}
      </ul>
      {done && <div className="px-3 py-1.5 text-[12px] border-t border-[#e3e8ef] bg-white">{ev.data.outside === 0 ? "Every row is inside what was asked." : `${ev.data.outside} of ${ev.data.total} rows are outside what was asked, so the action is refused.`}</div>}
    </div>
  );
}

const LABEL = { start: "Request", llm_request: "Asking the model", llm_response: "Model replied", llm_notice: "Model service", thought: "Thinking", agent_active: "Agent",
  access_wait: "Access", access_granted: "Access", access_denied: "Access", access_timeout: "Access", rejected_call: "Checked", tool_call: "Calling tool",
  tool_result: "Gateway answered", waiting_human: "Waiting", decision_update: "Decision", answer: "Replying", error: "Problem" };

function toneOf(ev) {
  if (ev.type === "pipeline") return ev.data.status || "info";
  const k = ev.data.kind;
  if (k === "error" || k === "access_denied" || k === "access_timeout") return "error";
  if (k === "llm_notice" || k === "rejected_call") return "warn";
  if (k === "tool_result") return ev.data.data?.verdict === "ALLOW" ? "ok" : ev.data.data?.verdict === "HOLD" ? "warn" : "denied";
  if (["access_wait", "access_granted", "waiting_human", "decision_update"].includes(k)) return "human";
  if (["llm_request", "llm_response"].includes(k)) return "model";
  return "agent";
}

function Line({ ev }) {
  if (ev.type === "sandbox") return <li className="pl-5"><SandboxBlock ev={ev} /></li>;
  const tone = toneOf(ev);
  const head = ev.type === "pipeline" ? "Gateway" : LABEL[ev.data.kind] || ev.data.kind;
  return (
    <li className="flex gap-2.5 py-1 text-[13px]">
      <span className={`w-2.5 h-2.5 rounded-full mt-1.5 shrink-0 ${COLOR[tone]}`} />
      <span className="text-[11px] text-[#94a3b8] w-[58px] shrink-0 pt-0.5">{t(ev.ts)}</span>
      <span className="min-w-0"><span className="text-[11px] font-semibold uppercase tracking-wide text-[#64748b] mr-1.5">{head}</span><span className={tone === "denied" || tone === "error" ? "text-[#b91c1c]" : "text-[#334155]"}>{ev.data.text}</span></span>
    </li>
  );
}

export default function ActivityFeed({ events, working }) {
  const end = useRef(null);
  useEffect(() => { end.current?.scrollIntoView({ block: "end" }); }, [events.length, working]);
  return (
    <div className="flex-1 overflow-auto px-5 py-4" role="log" aria-live="polite">
      {events.length === 0 && <p className="text-[13px] text-[#64748b]">Nothing yet. Send a request and every step appears here as it happens: the model's thinking, the access request, each check the gateway runs, and the sandbox result row by row.</p>}
      <ul className="space-y-0.5">{events.filter((e) => !(e.type === "agent" && ["start", "llm_request"].includes(e.data.kind))).map((e, i) => <Line key={e.id || i} ev={e} />)}</ul>
      {working && <div className="text-[13px] text-[#64748b] flex items-center gap-2 mt-2"><Icon name="refresh" size={14} className="animate-spin" />Working…</div>}
      <div ref={end} />
    </div>
  );
}
