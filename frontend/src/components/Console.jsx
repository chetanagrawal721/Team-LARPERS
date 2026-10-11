import DecisionCard from "./DecisionCard";

const dot = { ALLOW: "bg-emerald-400", HOLD: "bg-amber-400", BLOCK: "bg-rose-500", VOID: "bg-rose-500", DONE: "bg-emerald-400" };

export default function Console({ decisions, selectedId, onSelect, ...rest }) {
  const sel = decisions.find((d) => d.id === selectedId) || decisions[0];
  return (
    <section className="flex flex-col h-full min-h-0">
      <div className="px-4 py-2 text-xs uppercase tracking-wide text-slate-400 border-b border-slate-800">Moderator console</div>
      <div className="flex-1 overflow-auto p-4 space-y-4">
        <div>
          <div className="text-xs text-slate-500 mb-1">Live actions</div>
          <ul className="space-y-1 max-h-40 overflow-auto">
            {decisions.slice(0, 12).map((d) => (
              <li key={d.id}>
                <button onClick={() => onSelect(d.id)} className={`w-full text-left px-2 py-1 rounded flex items-center gap-2 text-sm ${sel?.id === d.id ? "bg-slate-800" : "hover:bg-slate-900"}`}>
                  <span className={`w-2.5 h-2.5 rounded-full ${dot[d.status === "void" ? "VOID" : d.verdict]}`} />
                  <span className="text-slate-400 w-20">{new Date(d.created_ts * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                  <span className="flex-1 truncate">{d.agent} · {d.action}</span>
                  <span className="text-xs text-slate-400">{d.status === "void" ? "VOID" : d.verdict} {d.rule}</span>
                </button>
              </li>
            ))}
            {decisions.length === 0 && <li className="text-slate-600 text-sm">Nothing yet.</li>}
          </ul>
        </div>
        {sel && <DecisionCard d={sel} {...rest} />}
      </div>
    </section>
  );
}
