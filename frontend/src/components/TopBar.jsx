import { USERS, getUser, setUser } from "../api";

const DOMAINS = [
  { id: "bank", icon: "🏦", tint: "#3b82f6" },
  { id: "hospital", icon: "🏥", tint: "#14b8a6" },
  { id: "shop", icon: "🛒", tint: "#f97316" },
];

export default function TopBar({ domain, org, onDomain, ai, onAi, page, onPage, online, onUser, onAudit }) {
  return (
    <header className="flex items-center gap-4 px-5 py-3 border-b border-slate-800 bg-slate-950">
      <div className="text-xl font-bold text-accent">🔏 SEALGATE</div>
      <nav className="flex gap-1">
        {[["gate", "Live Gate"], ["lab", "Attack Lab"]].map(([id, label]) => (
          <button key={id} onClick={() => onPage(id)}
                  className={`px-3 py-1 rounded ${page === id ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white"}`}>{label}</button>
        ))}
      </nav>
      <div className="flex items-center gap-1 ml-4">
        {DOMAINS.map((d) => (
          <button key={d.id} onClick={() => onDomain(d.id)} title={d.id}
                  className="px-3 py-1 rounded border text-lg"
                  style={{ borderColor: domain === d.id ? d.tint : "#334155", background: domain === d.id ? d.tint + "33" : "transparent" }}>{d.icon}</button>
        ))}
        <span className="ml-2 text-slate-300">{org}</span>
      </div>
      <div className="ml-auto flex items-center gap-4 text-sm">
        <button className="btn" onClick={onAudit}>Audit log</button>
        <label className="flex items-center gap-1 text-slate-400">acting as
          <select className="bg-slate-900 border border-slate-700 rounded px-1 py-0.5 text-slate-100" defaultValue={getUser().name}
                  onChange={(e) => { setUser(e.target.value); onUser && onUser(e.target.value); }}>
            {USERS.map((u) => <option key={u}>{u}</option>)}
          </select>
        </label>
        <button onClick={onAi} className="flex items-center gap-1">
          <span className={`inline-block w-2.5 h-2.5 rounded-full ${ai ? "bg-emerald-400" : "bg-slate-500"}`} /> AI {ai ? "on" : "off"}
        </button>
        <span className={online ? "text-emerald-400" : "text-rose-400"}>{online ? "● live" : "● offline"}</span>
      </div>
    </header>
  );
}
