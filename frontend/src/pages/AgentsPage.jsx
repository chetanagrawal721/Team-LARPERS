import { useEffect, useState } from "react";
import Icon from "../components/Icon";
import { AGENT_LABEL, ROLE_LABEL, call } from "../api";

const PILLS = { ACTIVE: "pill-allow", SHADOW: "pill-shadow", FROZEN: "pill-block" };

export default function AgentsPage({ refreshKey, notify }) {
  const [rows, setRows] = useState([]);
  const load = () => call("/agents").then(setRows).catch(() => {});
  useEffect(() => { load(); }, [refreshKey]);
  const unfreeze = async (a) => {
    try { await call(`/agents/${a.agent}/unfreeze`, { method: "POST", auth: true }); notify("ok", `${AGENT_LABEL(a.agent)} was unfrozen.`); load(); } catch (e) { notify("error", e.message); }
  };
  return (
    <div className="p-6 space-y-4 h-full overflow-auto">
      <div>
        <h1 className="text-[22px] font-semibold">Agents</h1>
        <p className="text-[13px] text-[#64748b]">Agent registry and live status. Agents hold no credentials; they can only propose actions.</p>
      </div>
      <div className="card overflow-auto">
        <table className="w-full text-[13px]">
          <thead><tr className="text-left text-[11px] uppercase tracking-wider text-[#64748b] border-b border-[#e3e8ef] bg-[#fafbfd]"><th className="px-5 py-2.5">Agent</th><th>Organisation</th><th>Allowed actions</th><th>Acts for</th><th>Status</th><th className="pr-5">Budget use</th></tr></thead>
          <tbody>
            {rows.map((a) => (
              <tr key={a.domain + a.agent} className="border-b border-[#f1f4f8]">
                <td className="px-5 py-3 font-semibold"><span className="inline-flex items-center gap-2"><span className="w-7 h-7 rounded-full bg-[#eef2f8] text-[#475569] grid place-items-center"><Icon name="agents" size={14} /></span>{AGENT_LABEL(a.agent)}</span></td>
                <td>{a.org}</td>
                <td className="text-[#475569] max-w-[260px]">{a.actions.join(", ")}</td>
                <td>{ROLE_LABEL(a.acts_for)}</td>
                <td><span className={`pill ${PILLS[a.status]}`}>{a.status}</span> {a.status === "FROZEN" && <button className="btn btn-quiet !py-0.5 !px-2 text-[#2563eb]" onClick={() => unfreeze(a)}>Unfreeze</button>}</td>
                <td className="pr-5 w-[170px]">
                  <div className="flex items-center gap-2"><div className="h-1.5 flex-1 rounded bg-[#eef1f6]"><div className={`h-full rounded ${a.budget_pct > 80 ? "bg-[#dc2626]" : "bg-[#2563eb]"}`} style={{ width: `${a.budget_pct}%` }} /></div><span className="w-9 text-right text-[#475569]">{a.budget_pct}%</span></div>
                </td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={6} className="px-5 py-8 text-center text-[#64748b]">Loading…</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
