import { useState } from "react";
import Icon from "./Icon";
import { ACTION_LABEL, AGENT_LABEL, PILL, clock, stateOf, summaryOf } from "../api";

const FILTERS = [["all", "All", () => true], ["approval", "Needs approval", (d) => d.verdict === "HOLD" && d.status === "pending"],
  ["blocked", "Blocked", (d) => d.verdict === "BLOCK" || d.status === "void"], ["shadow", "Shadow", (d) => d.status === "shadow"]];

export default function ActionStream({ decisions, selectedId, onSelect }) {
  const [f, setF] = useState("all");
  const test = FILTERS.find((x) => x[0] === f)[2];
  const shown = decisions.filter(test);
  return (
    <section className="card flex flex-col min-h-0" aria-label="Action stream">
      <div className="px-5 pt-4 pb-3 flex items-center justify-between">
        <h2 className="font-semibold">Action stream</h2>
        <span className="text-[12px] text-[#64748b]">newest first</span>
      </div>
      <div className="px-5 flex flex-wrap gap-2 pb-3" role="tablist">
        {FILTERS.map(([id, label, t]) => (
          <button key={id} role="tab" aria-selected={f === id} onClick={() => setF(id)}
                  className={`chip ${f === id ? "bg-[#e8f0ff] border-[#bcd2ff] text-[#1d4ed8]" : "border-[#e3e8ef] text-[#475569] hover:bg-[#f8fafc]"}`}>
            {label} ({decisions.filter(t).length})
          </button>
        ))}
      </div>
      <ul className="flex-1 overflow-auto border-t border-[#eef1f6]">
        {shown.map((d) => {
          const v = stateOf(d); const active = d.id === selectedId;
          return (
            <li key={d.id}>
              <button onClick={() => onSelect(d.id)} aria-current={active} aria-label={`${AGENT_LABEL(d.agent)} ${d.action}, ${v}`}
                      className={`w-full text-left px-5 py-3 flex items-center gap-3 border-l-[3px] border-b border-b-[#f1f4f8] ${active ? "bg-[#f3f7ff] border-l-[#2563eb]" : "border-l-transparent hover:bg-[#f8fafc]"}`}>
                <span className="text-[12px] text-[#64748b] w-[62px] shrink-0 whitespace-nowrap">{clock(d.created_ts)}</span>
                <span className="w-8 h-8 rounded-full bg-[#eef2f8] text-[#475569] grid place-items-center shrink-0"><Icon name="agents" size={16} /></span>
                <span className="flex-1 min-w-0">
                  <span className="block text-[13px] font-semibold truncate">{AGENT_LABEL(d.agent)}</span>
                  <span className="block text-[12px] text-[#64748b] truncate">{ACTION_LABEL[d.action] || d.action}{summaryOf(d) ? ` · ${summaryOf(d)}` : ""}</span>
                </span>
                <span className={`pill ${PILL[v]}`}>{v}</span>
              </button>
            </li>
          );
        })}
        {shown.length === 0 && <li className="px-5 py-8 text-center text-[13px] text-[#64748b]">{decisions.length ? "Nothing matches this filter." : "No actions yet. Use “Ask an agent” to start one."}</li>}
      </ul>
    </section>
  );
}
