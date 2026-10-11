import { useEffect, useRef, useState } from "react";
import Icon from "./Icon";
import { USERS, setUser } from "../api";
import { useUser } from "../hooks/useUser";

function useOutside(ref, close) {
  useEffect(() => {
    const h = (e) => { if (ref.current && !ref.current.contains(e.target)) close(); };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, [ref, close]);
}

export function OrgMenu({ orgs, current, onPick, onClose, className = "absolute z-50 mt-2" }) {
  const ref = useRef(null);
  useOutside(ref, onClose);
  return (
    <div ref={ref} className={`${className} w-[300px] card p-1.5 shadow-lg`} role="menu">
      {orgs.map((o) => (
        <button key={o.domain} role="menuitem" onClick={() => { onPick(o.domain); onClose(); }}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-[#f1f5f9] text-left">
          <span className="w-4 text-[#2563eb]">{o.domain === current && <Icon name="check" size={14} />}</span>
          <span className="flex-1 text-[13px] font-medium">{o.org}</span>
          <span className="text-[12px] text-[#64748b]">Policy v{o.version}</span>
          {o.domain === current && <span className="pill pill-allow">Verified</span>}
        </button>
      ))}
    </div>
  );
}

export default function TopBar({ pendingAccess = 0, onOpenAccess, orgs, domain, onDomain, ai, onAi, online, waiting, waitingList, onOpenWaiting, onUser, menuOpen, setMenuOpen }) {
  const [bell, setBell] = useState(false);
  const [who, setWho] = useState(false);
  const user = useUser();
  const bellRef = useRef(null), whoRef = useRef(null);
  useOutside(bellRef, () => setBell(false));
  useOutside(whoRef, () => setWho(false));
  const org = orgs.find((o) => o.domain === domain);
  const me = USERS.find((u) => u.id === user) || USERS[0];
  return (
    <header className="h-14 shrink-0 bg-white border-b border-[#e3e8ef] flex items-center gap-4 px-6">
      <div className="relative">
        <button onClick={() => setMenuOpen(!menuOpen)} className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-[#f1f5f9]" aria-haspopup="menu" aria-expanded={menuOpen}>
          <span className="font-semibold">{org?.org || "Organisation"}</span>
          <span className="text-[12px] text-[#64748b]">Policy v{org?.version ?? "-"}</span>
          <span className="pill pill-allow">Verified</span>
          <Icon name="chevron" size={14} className="text-[#94a3b8]" />
        </button>
        {menuOpen && <OrgMenu orgs={orgs} current={domain} onPick={onDomain} onClose={() => setMenuOpen(false)} />}
      </div>
      <div className="ml-auto flex items-center gap-5">
        {!online && <span className="text-[12px] text-[#b91c1c]">Disconnected</span>}
        {pendingAccess > 0 && <button className="pill pill-info !py-1 !px-2.5 text-[12px]" onClick={onOpenAccess}>{pendingAccess} agent{pendingAccess === 1 ? "" : "s"} waiting for access</button>}
        <button onClick={onAi} className="flex items-center gap-2 text-[13px]" title="AI can only make a decision stricter. Turn it off and nothing gets less safe.">
          <span className={`w-2 h-2 rounded-full ${ai ? "bg-[#16a34a]" : "bg-[#94a3b8]"}`} />
          <span className="text-[#475569]">AI assist:</span><b className={ai ? "text-[#15803d]" : "text-[#64748b]"}>{ai ? "On" : "Off"}</b>
        </button>
        <div className="relative" ref={bellRef}>
          <button onClick={() => setBell(!bell)} className="relative p-2 rounded-lg hover:bg-[#f1f5f9]" aria-label={`Notifications, ${waiting} waiting`}>
            <Icon name="bell" />
            {waiting > 0 && <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 px-1 rounded-full bg-[#dc2626] text-white text-[10px] font-bold grid place-items-center">{waiting}</span>}
          </button>
          {bell && (
            <div className="absolute right-0 mt-2 w-[330px] card p-2 shadow-lg z-50">
              <div className="h-label px-2 py-1">Waiting for a decision</div>
              {waitingList.length === 0 && <div className="px-2 py-3 text-[13px] text-[#64748b]">Nothing is waiting.</div>}
              {waitingList.slice(0, 6).map((d) => (
                <button key={d.id} onClick={() => { onOpenWaiting(d); setBell(false); }} className="w-full text-left px-2 py-2 rounded-lg hover:bg-[#f1f5f9] text-[13px]">
                  <b>{d.agent}</b> · {d.action}<div className="text-[12px] text-[#64748b] truncate">{d.reason}</div>
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="relative" ref={whoRef}>
          <button onClick={() => setWho(!who)} className="flex items-center gap-2 pl-1 pr-2 py-1 rounded-lg hover:bg-[#f1f5f9]" aria-haspopup="menu">
            <span className="w-8 h-8 rounded-full bg-[#2563eb] text-white grid place-items-center text-[13px] font-semibold">{me.name[0]}</span>
            <span className="text-left leading-tight"><span className="block text-[13px] font-semibold">{me.name.split(" ")[0]}</span><span className="block text-[11px] text-[#64748b]">{me.role}</span></span>
            <Icon name="chevron" size={14} className="text-[#94a3b8]" />
          </button>
          {who && (
            <div className="absolute right-0 mt-2 w-[250px] card p-1.5 shadow-lg z-50" role="menu">
              <div className="h-label px-2 py-1">Act as (demo sign-in)</div>
              {USERS.map((u) => (
                <button key={u.id} role="menuitem" onClick={() => { setUser(u.id); setWho(false); onUser && onUser(u.id); }}
                        className="w-full flex items-center gap-2 px-2 py-2 rounded-lg hover:bg-[#f1f5f9] text-left">
                  <span className="w-4 text-[#2563eb]">{u.id === user && <Icon name="check" size={14} />}</span>
                  <span className="flex-1"><span className="block text-[13px] font-medium">{u.name}</span><span className="block text-[11px] text-[#64748b]">{u.role}</span></span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
