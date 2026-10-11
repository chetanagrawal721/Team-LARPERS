import DecisionCard from "./DecisionCard";
import { headline } from "../api";

const COLOR = { ALLOW: "#1a7f37", HOLD: "#9a6700", BLOCK: "#cf222e", VOID: "#cf222e", DONE: "#1a7f37" };
const WORD = { ALLOW: "Allowed", HOLD: "Waiting", BLOCK: "Blocked", VOID: "Voided", DONE: "Done" };

export default function Console({ decisions, selectedId, onSelect, ...rest }) {
  const sel = decisions.find((d) => d.id === selectedId) || decisions[0];
  const waiting = decisions.filter((d) => d.verdict === "HOLD" && d.status === "pending").length;
  return (
    <section className="flex flex-col h-full min-h-0" aria-label="Moderator console">
      <div className="px-4 py-2 border-b border-[#d0d7de] flex items-center justify-between">
        <span className="label">Moderator console</span>
        {waiting > 0 && <span className="text-[12px] text-[#9a6700]">{waiting} waiting for a decision</span>}
      </div>
      <div className="flex-1 overflow-auto">
        <ul className="border-b border-[#d0d7de] max-h-44 overflow-auto" aria-label="Recent actions">
          {decisions.slice(0, 15).map((d) => {
            const v = d.status === "void" ? "VOID" : d.verdict;
            const active = sel?.id === d.id;
            return (
              <li key={d.id}>
                <button onClick={() => onSelect(d.id)} aria-current={active} className={`w-full text-left px-4 py-1.5 flex items-center gap-3 text-[13px] border-l-2 ${active ? "bg-[#ddeeff] border-[#0969da]" : "border-transparent hover:bg-[#f6f8fa]"}`}>
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ background: COLOR[v] }} />
                  <span className="text-[#59636e] w-[4.5rem] shrink-0 whitespace-nowrap">{new Date(d.created_ts * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                  <span className="flex-1 truncate">{headline(d)}</span>
                  <span className="text-[12px] shrink-0" style={{ color: COLOR[v] }}>{WORD[v]}</span>
                </button>
              </li>
            );
          })}
          {decisions.length === 0 && <li className="px-4 py-3 text-[13px] text-[#59636e]">No actions yet. Run a scenario on the left.</li>}
        </ul>
        <div className="p-4">{sel && <DecisionCard d={sel} {...rest} />}</div>
      </div>
    </section>
  );
}
