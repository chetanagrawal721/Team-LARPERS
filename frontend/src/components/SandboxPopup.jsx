import { useEffect, useRef, useState } from "react";
import { num, rupees } from "../api";

const reduced = () => typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

// A temporary window that replays the sandbox run like a code review: each row the action would change appears as a diff line,
// green when it is inside what the user asked for and red when it is outside. When it finishes it shows the verdict and closes.
export default function SandboxPopup({ ev, onClose, replay = false }) {
  const rows = ev.data.rows || [];
  const total = ev.data.total || rows.length;
  const [shown, setShown] = useState(0);
  const [phase, setPhase] = useState("run");       // run -> verdict -> closing
  const list = useRef(null);
  const outsideAll = ev.data.outside || 0;

  useEffect(() => {
    if (reduced()) { setShown(rows.length); setPhase("verdict"); return; }
    const duration = Math.min(5200, Math.max(2600, rows.length * 38));      // slow enough to read, never tedious
    const tick = 40;
    const step = Math.max(1, Math.ceil(rows.length / (duration / tick)));
    const id = setInterval(() => setShown((n) => {
      const next = Math.min(rows.length, n + step);
      if (next >= rows.length) { clearInterval(id); setTimeout(() => setPhase("verdict"), 450); }
      return next;
    }), tick);
    return () => clearInterval(id);
  }, [ev.id]);

  useEffect(() => { if (phase === "verdict") { const t = setTimeout(() => { setPhase("closing"); setTimeout(onClose, 350); }, replay ? 2600 : 1900); return () => clearTimeout(t); } }, [phase]);
  useEffect(() => { if (list.current) list.current.scrollTop = list.current.scrollHeight; }, [shown]);
  useEffect(() => { const h = (e) => e.key === "Escape" && onClose(); window.addEventListener("keydown", h); return () => window.removeEventListener("keydown", h); }, [onClose]);

  const seen = rows.slice(0, shown);
  const inside = seen.filter((r) => r.inside).length;
  const outside = seen.length - inside;
  const pct = rows.length ? Math.round((100 * shown) / rows.length) : 100;
  const bad = outsideAll > 0;

  return (
    <div className={`fixed inset-0 z-[70] bg-[#0f172a]/55 grid place-items-center p-6 ${phase === "closing" ? "popup-out" : "popup-in"}`} role="dialog" aria-modal="true" aria-label="Sandbox run">
      <div className="w-full max-w-[860px] rounded-xl overflow-hidden shadow-2xl border border-[#d0d7de] bg-white">
        <div className="px-5 py-3 bg-[#0f172a] text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="flex gap-1.5"><i className="w-2.5 h-2.5 rounded-full bg-[#f85149]" /><i className="w-2.5 h-2.5 rounded-full bg-[#d29922]" /><i className="w-2.5 h-2.5 rounded-full bg-[#3fb950]" /></span>
            <span className="font-mono text-[13px]">sandbox · {ev.data.agent} → {ev.data.action}</span>
          </div>
          <div className="flex items-center gap-3 text-[12px]">
            <span className="px-2 py-0.5 rounded bg-[#1f2a44] text-[#9db4ff]">COPY OF THE DATABASE · real data untouched</span>
            <button className="text-[#9db4ff] hover:text-white" onClick={onClose}>Skip</button>
          </div>
        </div>

        <div className="h-1.5 bg-[#e5e7eb]"><div className={`h-full transition-[width] duration-100 ${bad ? "bg-[#dc2626]" : "bg-[#16a34a]"}`} style={{ width: `${pct}%` }} /></div>

        <div className="px-5 py-2.5 flex items-center justify-between text-[13px] border-b border-[#e3e8ef] bg-[#f8fafc]">
          <span>Applying the proposed change to the copy…</span>
          <span className="font-mono"><b className="text-[#15803d]">+{inside} approved</b> &nbsp; <b className="text-[#b91c1c]">−{outside} denied</b> &nbsp; <span className="text-[#64748b]">{shown}/{rows.length}{total > rows.length ? ` (of ${num(total)})` : ""}</span></span>
        </div>

        <ul ref={list} className="h-[300px] overflow-hidden font-mono text-[12.5px] bg-white">
          {seen.map((r, i) => (
            <li key={i} className={`px-5 py-[3px] flex gap-3 ${r.inside ? "row-ok text-[#14532d]" : "row-bad text-[#7f1d1d]"}`}>
              <span className="w-4 font-bold">{r.inside ? "+" : "−"}</span>
              <span className="w-[110px] shrink-0 truncate">{r.pk}</span>
              <span className="w-[64px] shrink-0 opacity-70">{r.who}</span>
              <span className="flex-1 truncate">{r.name}</span>
              <span className="shrink-0">{r.amount_minor != null ? rupees(r.amount_minor) : ""}</span>
              <span className="w-[72px] text-right font-semibold">{r.inside ? "APPROVED" : "DENIED"}</span>
            </li>
          ))}
        </ul>

        <div className={`px-5 py-3 border-t border-[#e3e8ef] flex items-center justify-between transition-opacity duration-300 ${phase === "run" ? "opacity-30" : "opacity-100"}`}>
          <div className="text-[14px]">
            {phase === "run" ? "Measuring…" : bad ? <><b className="text-[#b91c1c]">{num(outsideAll)} of {num(total)} rows are outside what the user asked for.</b> The change is refused.</> : <b className="text-[#15803d]">Every row is inside what the user asked for.</b>}
          </div>
          {phase !== "run" && <span className={`stamp ${bad ? "stamp-bad" : "stamp-ok"}`}>{bad ? "REJECTED" : "WITHIN REQUEST"}</span>}
        </div>
      </div>
    </div>
  );
}
