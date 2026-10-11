const DOMAINS = [["bank", "Bank"], ["hospital", "Hospital"], ["shop", "Shop"]];

const Mark = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
    <circle cx="12" cy="12" r="9.5" fill="none" stroke="#58a6ff" strokeWidth="2" />
    <path d="M7.5 12.3l3 3 6-6.5" fill="none" stroke="#58a6ff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export default function TopBar({ domain, org, onDomain, ai, onAi, page, onPage, online, onAudit }) {
  const tab = (active) => `px-3 py-1.5 text-[13px] border-b-2 -mb-px ${active ? "border-[#58a6ff] text-white" : "border-transparent text-[#8b949e] hover:text-[#e6edf3]"}`;
  return (
    <header className="flex items-end gap-6 px-5 pt-3 border-b border-[#30363d] bg-[#0d1117]">
      <div className="flex items-center gap-2 pb-2.5"><Mark /><span className="font-semibold tracking-wide">SEALGATE</span></div>
      <nav className="flex" aria-label="Pages">
        <button className={tab(page === "gate")} onClick={() => onPage("gate")}>Live gate</button>
        <button className={tab(page === "lab")} onClick={() => onPage("lab")}>Attack lab</button>
      </nav>
      <div className="flex items-center gap-1 pb-2" role="group" aria-label="Organisation">
        <span className="text-[12px] text-[#8b949e] mr-1">Organisation</span>
        {DOMAINS.map(([id, label]) => (
          <button key={id} onClick={() => onDomain(id)} aria-pressed={domain === id}
                  className={`px-2.5 py-1 rounded-md text-[13px] ${domain === id ? "bg-[#21262d] text-white border border-[#30363d]" : "text-[#8b949e] hover:text-white border border-transparent"}`}>{label}</button>
        ))}
        <span className="text-[12px] text-[#8b949e] ml-2">{org}</span>
      </div>
      <div className="ml-auto flex items-center gap-4 pb-2 text-[13px]">
        <button className="btn btn-quiet" onClick={onAudit}>Audit log</button>
        <button className="btn btn-quiet" onClick={onAi} title="AI can only make decisions stricter. Turn it off and nothing gets less safe.">
          AI checks: <b className={ai ? "text-[#56d364]" : "text-[#8b949e]"}>{ai ? "on" : "off"}</b>
        </button>
        <span className={`flex items-center gap-1.5 ${online ? "text-[#8b949e]" : "text-[#ff7b72]"}`}>
          <span className={`w-2 h-2 rounded-full ${online ? "bg-[#3fb950]" : "bg-[#f85149]"}`} />{online ? "Connected" : "Disconnected"}
        </span>
      </div>
    </header>
  );
}
