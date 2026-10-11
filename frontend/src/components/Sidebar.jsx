import Icon from "./Icon";

const ITEMS = [["gate", "Live Gate", "live"], ["lab", "Attack Lab", "lab"], ["activity", "Agent Activity", "chat"], ["audit", "Audit", "audit"], ["policy", "Policy", "policy"], ["agents", "Agents", "agents"]];

export default function Sidebar({ page, onPage, org, onOrg, waiting }) {
  return (
    <aside className="w-[210px] shrink-0 bg-white border-r border-[#e3e8ef] flex flex-col" aria-label="Main navigation">
      <div className="flex items-center gap-2 px-5 h-14 border-b border-[#e3e8ef]">
        <span className="w-7 h-7 rounded-lg bg-[#2563eb] text-white grid place-items-center"><Icon name="shield" size={16} /></span>
        <span className="font-bold tracking-wide">SEALGATE</span>
      </div>
      <nav className="p-3 space-y-1 flex-1">
        {ITEMS.map(([id, label, icon]) => (
          <button key={id} onClick={() => onPage(id)} aria-current={page === id ? "page" : undefined}
                  className={`nav-item ${page === id ? "nav-item-active" : ""}`}>
            <Icon name={icon} />{label}
            {id === "gate" && waiting > 0 && <span className="ml-auto pill pill-hold">{waiting}</span>}
          </button>
        ))}
      </nav>
      <button onClick={onOrg} className="m-3 flex items-center gap-2 px-3 py-2 rounded-lg border border-[#e3e8ef] text-left hover:bg-[#f8fafc]" title="Switch organisation">
        <span className="w-6 h-6 rounded bg-[#e0ecff] text-[#1d4ed8] grid place-items-center text-[11px] font-bold">{(org || "?")[0]}</span>
        <span className="flex-1 truncate text-[13px] font-medium">{org || "Organisation"}</span>
        <Icon name="chevron" size={14} className="text-[#94a3b8]" />
      </button>
    </aside>
  );
}
