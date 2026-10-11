import { useEffect, useState } from "react";
import Icon from "../components/Icon";
import { AGENT_LABEL, ROLE_LABEL, call } from "../api";

const PILLS = { ACTIVE: "pill-allow", SHADOW: "pill-shadow", FROZEN: "pill-block" };

function Section({ title, children }) {
  return <div><div className="h-label mb-1.5">{title}</div>{children}</div>;
}

function AgentCard({ a, requests, onUnfreeze }) {
  const [prompt, setPrompt] = useState(false);
  const mine = requests.filter((r) => r.agent === a.agent);
  const granted = mine.filter((r) => r.status === "granted").length, denied = mine.filter((r) => r.status === "denied").length, waiting = mine.filter((r) => r.status === "pending").length;
  return (
    <article className="card p-5 space-y-4">
      <header className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className="w-10 h-10 rounded-full bg-[#eef2f8] text-[#475569] grid place-items-center shrink-0"><Icon name="agents" size={18} /></span>
          <div>
            <h2 className="text-[16px] font-semibold">{a.display_name} <span className="font-mono text-[12px] text-[#64748b] font-normal">{a.agent}</span></h2>
            <p className="text-[13px] text-[#475569]">{a.role}</p>
            <p className="text-[12px] text-[#64748b] mt-0.5">{a.org} · acts for {a.acts_for ? ROLE_LABEL(a.acts_for) : "nobody"}</p>
          </div>
        </div>
        <div className="text-right">
          <span className={`pill ${PILLS[a.status]}`}>{a.status}</span>
          {a.status === "FROZEN" && <div><button className="btn btn-quiet !py-0.5 !px-2 text-[#2563eb]" onClick={() => onUnfreeze(a)}>Unfreeze</button></div>}
        </div>
      </header>

      <div className="grid md:grid-cols-2 gap-5 text-[13px]">
        <Section title="What it does"><ul className="list-disc ml-4 space-y-0.5">{a.does.map((x) => <li key={x}>{x}</li>)}</ul></Section>
        <Section title="What it cannot do"><ul className="list-disc ml-4 space-y-0.5 text-[#475569]">{a.cannot.map((x) => <li key={x}>{x}</li>)}</ul></Section>
      </div>

      <Section title="Tools it owns">
        <div className="space-y-2">
          {a.tools.map((t) => (
            <div key={t.name} className="rounded-lg border border-[#e3e8ef] p-3 text-[13px]">
              <div className="flex items-center justify-between"><b className="font-mono text-[12px]">{t.name}</b><span className="pill pill-neutral">{t.action}</span></div>
              <p className="text-[#475569] mt-0.5">{t.description}</p>
              <ul className="mt-1.5 text-[12px] text-[#64748b] space-y-0.5">
                {Object.entries(t.params).map(([k, v]) => <li key={k}><b className="text-[#334155]">{k}</b>{t.required.includes(k) ? " (required)" : ""}: {v}</li>)}
              </ul>
            </div>
          ))}
        </div>
      </Section>

      <div className="grid md:grid-cols-3 gap-4 text-[13px]">
        <Section title="Access requests">
          <div className="flex gap-3"><span><b>{granted}</b> granted</span><span><b>{denied}</b> denied</span><span className={waiting ? "text-[#b45309] font-semibold" : ""}><b>{waiting}</b> waiting</span></div>
          <p className="text-[12px] text-[#64748b] mt-1">A person grants access before every proposal.</p>
        </Section>
        <Section title="Always needs a human">
          <p>{a.protected.length ? `Protected actions: ${a.protected.join(", ")}.` : "Every action needs approval of its measured effect; none is exempt."}</p>
        </Section>
        <Section title="Budget used (this hour)">
          <div className="flex items-center gap-2"><div className="h-1.5 flex-1 rounded bg-[#eef1f6]"><div className={`h-full rounded ${a.budget_pct > 80 ? "bg-[#dc2626]" : "bg-[#2563eb]"}`} style={{ width: `${a.budget_pct}%` }} /></div><span className="w-9 text-right">{a.budget_pct}%</span></div>
        </Section>
      </div>

      <div>
        <button className="btn" onClick={() => setPrompt(!prompt)}>{prompt ? "Hide" : "Show"} this agent's prompt</button>
        {prompt && <pre className="mt-2 text-[12px] leading-5 whitespace-pre-wrap bg-[#f8fafc] border border-[#e3e8ef] rounded-lg p-3 max-h-[320px] overflow-auto">{a.prompt}</pre>}
      </div>
    </article>
  );
}

export default function AgentsPage({ refreshKey, notify, access }) {
  const [rows, setRows] = useState([]);
  const load = () => call("/agents").then(setRows).catch(() => {});
  useEffect(() => { load(); }, [refreshKey]);
  const unfreeze = async (a) => {
    try { await call(`/agents/${a.agent}/unfreeze`, { method: "POST", auth: true }); notify("ok", `${AGENT_LABEL(a.agent)} was unfrozen.`); load(); } catch (e) { notify("error", e.message); }
  };
  const orgs = [...new Set(rows.map((r) => r.org))];
  return (
    <div className="p-6 space-y-5 h-full overflow-auto">
      <div>
        <h1 className="text-[22px] font-semibold">Agents</h1>
        <p className="text-[13px] text-[#64748b]">What each agent is for, what it may do, the tools it owns and its prompt. Agents never start work on their own: each one asks for access in the chat, and a person decides.</p>
      </div>
      {rows.length === 0 && <p className="text-[#64748b]">Loading…</p>}
      {orgs.map((org) => (
        <section key={org} className="space-y-3">
          <h2 className="text-[14px] font-semibold text-[#475569]">{org}</h2>
          {rows.filter((r) => r.org === org).map((a) => <AgentCard key={a.agent + a.domain} a={a} requests={access || []} onUnfreeze={unfreeze} />)}
        </section>
      ))}
    </div>
  );
}
