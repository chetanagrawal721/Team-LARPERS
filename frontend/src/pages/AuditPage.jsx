import { useEffect, useState } from "react";
import Icon from "../components/Icon";
import { PILL, call, clock, pathLabel } from "../api";

const DOT = { done: "bg-[#2563eb]", failed: "bg-[#dc2626]", pending: "bg-[#d97706]", skipped: "bg-[#cbd5e1]" };

export default function AuditPage({ refreshKey }) {
  const [rows, setRows] = useState([]);
  const [q, setQ] = useState("");
  const [sel, setSel] = useState(null);
  const [ev, setEv] = useState(null);
  const [tab, setTab] = useState("trail");
  const [verify, setVerify] = useState(null);
  const [replay, setReplay] = useState(null);
  const load = () => call("/audit?limit=200").then((r) => { setRows(r); setSel((s) => s ?? r[0]?.seq ?? null); }).catch(() => {});
  useEffect(() => { load(); }, [refreshKey]);
  useEffect(() => { if (sel != null) { setReplay(null); call(`/audit/${sel}/evidence`).then(setEv).catch(() => setEv(null)); } }, [sel, refreshKey]);
  const shown = rows.filter((r) => !q || `${r.seq} ${r.agent} ${r.action} ${r.decision} ${r.rule}`.toLowerCase().includes(q.toLowerCase()));
  const broken = verify && !verify.ok ? verify.first_broken_seq : null;

  return (
    <div className="p-6 space-y-4 h-full overflow-auto">
      <div>
        <h1 className="text-[22px] font-semibold">Audit & evidence</h1>
        <p className="text-[13px] text-[#64748b]">Why was this action allowed or blocked? Follow the full chain of events.</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-[minmax(300px,4fr)_8fr] gap-5 items-start">
        <section className="card flex flex-col lg:max-h-[calc(100vh-190px)]" aria-label="Audit entries">
          <div className="p-4 relative">
            <Icon name="search" size={15} className="absolute left-7 top-[26px] text-[#94a3b8]" />
            <input className="field !pl-9" placeholder="Search by ID, agent or action" aria-label="Search the audit log" value={q} onChange={(e) => setQ(e.target.value)} />
          </div>
          <ul className="overflow-auto border-t border-[#eef1f6]">
            {shown.map((r) => (
              <li key={r.seq}>
                <button onClick={() => setSel(r.seq)} aria-current={sel === r.seq} className={`w-full text-left px-4 py-3 border-l-[3px] border-b border-b-[#f1f4f8] flex items-center gap-3 ${sel === r.seq ? "bg-[#f3f7ff] border-l-[#2563eb]" : "border-l-transparent hover:bg-[#f8fafc]"} ${broken != null && r.seq >= broken ? "!bg-[#fff5f5]" : ""}`}>
                  <span className="flex-1 min-w-0">
                    <span className="block text-[13px] font-semibold">#A-{r.seq} <span className="font-normal text-[#475569]">{r.agent}</span></span>
                    <span className="block text-[12px] text-[#64748b]">{clock(r.ts)} · {r.action.replace(/_/g, " ")}</span>
                  </span>
                  <span className={`pill ${PILL[r.decision] || "pill-neutral"}`}>{r.decision}</span>
                </button>
              </li>
            ))}
            {shown.length === 0 && <li className="px-4 py-8 text-center text-[13px] text-[#64748b]">No entries.</li>}
          </ul>
        </section>

        <section className="card p-5 min-h-[420px]" aria-label="Evidence">
          {!ev ? <p className="text-[#64748b]">Select an entry to see its evidence.</p> : (
            <>
              <div className="flex items-start justify-between gap-3 mb-1">
                <div>
                  <h2 className="text-[17px] font-semibold flex items-center gap-2 flex-wrap">#A-{ev.seq} <span className="font-normal text-[#475569]">{ev.agent}</span>
                    <span className={`pill ${PILL[ev.decision] || "pill-neutral"}`}>{ev.decision} · {ev.rule}</span></h2>
                  <p className="text-[12px] text-[#64748b]">{ev.headline || ev.action} · {new Date(ev.when * 1000).toLocaleString()}</p>
                </div>
                <div className="flex items-center gap-2">
                  <button className="btn" onClick={async () => { try { setReplay(await call(`/audit/replay/${ev.seq}`, { method: "POST" })); } catch (e) { setReplay({ error: e.message }); } }}>Replay</button>
                  <button className="btn btn-primary" onClick={async () => setVerify(await call("/audit/verify", { method: "POST" }))}>Verify</button>
                </div>
              </div>
              {(verify || replay) && (
                <div className="flex flex-wrap gap-4 text-[13px] mb-2">
                  {verify && (verify.ok ? <span className="text-[#15803d]">Chain intact</span> : <span className="text-[#b91c1c]">Chain broken at #A-{verify.first_broken_seq}</span>)}
                  {replay && (replay.error ? <span className="text-[#b91c1c]">{replay.error}</span> : replay.reproduced === true ? <span className="text-[#15803d]">Replay reproduced the same decision from the stored inputs</span> : replay.reproduced === false ? <span className="text-[#b91c1c]">Replay MISMATCH</span> : <span className="text-[#64748b]">This entry is not a decision, so there is nothing to replay</span>)}
                </div>
              )}
              <div className="flex gap-6 border-b border-[#e3e8ef] my-3" role="tablist">
                {[["trail", "Evidence trail"], ["prov", "Provenance"]].map(([id, l]) => <button key={id} role="tab" aria-selected={tab === id} className={`tab ${tab === id ? "tab-active" : ""}`} onClick={() => setTab(id)}>{l}</button>)}
              </div>
              {tab === "trail" ? (
                <ol className="space-y-0">
                  {ev.steps.map((s, i) => (
                    <li key={s.key} className="flex gap-3">
                      <div className="flex flex-col items-center"><span className={`w-3 h-3 rounded-full mt-1.5 ${DOT[s.state]}`} />{i < ev.steps.length - 1 && <span className="w-px flex-1 bg-[#e3e8ef]" />}</div>
                      <div className="pb-4 flex-1 min-w-0 grid grid-cols-[130px_1fr] gap-3 text-[13px]"><div className="font-medium">{s.key}</div><div className="text-[#334155]">{s.text}</div></div>
                    </li>
                  ))}
                </ol>
              ) : (
                <div className="space-y-3 text-[13px]">
                  <div><div className="h-label mb-1">Data labels</div>{ev.labels?.length ? ev.labels.join(", ") : "none"}</div>
                  <div><div className="h-label mb-1">Where the data came from</div>{ev.provenance?.length ? <ul className="list-disc ml-4">{ev.provenance.map((p) => <li key={p}>{p}</li>)}</ul> : "No tracked data path for this action."}</div>
                  <div><div className="h-label mb-1">Chain</div><div className="font-mono text-[12px] text-[#475569] break-all">previous {ev.prev_hash.slice(0, 16)}… → this {ev.entry_hash.slice(0, 16)}…</div><div className="font-mono text-[12px] text-[#475569]">policy {ev.policy_hash.slice(0, 16)}…</div></div>
                </div>
              )}
              <div className="mt-2 pt-3 border-t border-[#eef1f6] text-[12px] text-[#64748b] flex flex-wrap gap-x-4">
                <span>Result: <b className="text-[#0f172a]">{ev.result}</b></span><span>Path: {pathLabel(ev.path)}</span>{ev.labels?.length > 0 && <span>Labels: {ev.labels.join(", ")}</span>}
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
