import { useEffect, useState } from "react";
import { call, rupees } from "../api";

const KV = ({ k, v }) => <div className="flex justify-between gap-4 py-2 border-b border-[#f1f4f8] text-[13px]"><span className="text-[#64748b]">{k}</span><span className="font-medium text-right break-all">{v}</span></div>;

export default function PolicyPage({ domain, onSwitchOrg }) {
  const [p, setP] = useState(null);
  const [tab, setTab] = useState("yaml");
  useEffect(() => { call(`/policy?domain=${domain}`).then(setP).catch(() => setP(null)); }, [domain]);
  if (!p) return <div className="p-6 text-[#64748b]">Loading the policy…</div>;
  const env = Object.entries(p.limits.envelopes);

  return (
    <div className="p-6 space-y-4 h-full overflow-auto">
      <div>
        <h1 className="text-[22px] font-semibold">Policy file <span className="text-[13px] font-normal text-[#64748b]">(read-only)</span></h1>
        <p className="text-[13px] text-[#64748b]">The single file that governs {p.org}. Changes are made in the repository, reviewed by two people and logged.</p>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-[8fr_3.2fr] gap-5 items-start">
        <section className="card p-5">
          <div className="flex gap-6 border-b border-[#e3e8ef] mb-4" role="tablist">
            {[["yaml", "YAML"], ["limits", "Limits"], ["labels", "Labels"], ["budgets", "Budgets"]].map(([id, l]) => <button key={id} role="tab" aria-selected={tab === id} className={`tab ${tab === id ? "tab-active" : ""}`} onClick={() => setTab(id)}>{l}</button>)}
          </div>
          {tab === "yaml" && (
            <pre className="text-[12px] leading-5 font-mono bg-[#f8fafc] border border-[#e3e8ef] rounded-lg p-4 overflow-auto max-h-[60vh]">
              {p.yaml.split("\n").map((line, i) => <div key={i} className="flex"><span className="w-8 shrink-0 text-right pr-3 text-[#94a3b8] select-none">{i + 1}</span><span className="whitespace-pre-wrap break-all">{line}</span></div>)}
            </pre>
          )}
          {tab === "limits" && (
            <div className="space-y-4 text-[13px]">
              <table className="w-full"><thead><tr className="text-left text-[11px] uppercase tracking-wider text-[#64748b] border-b border-[#e3e8ef]"><th className="py-2">Action</th><th>Max rows</th><th>Max amount</th></tr></thead>
                <tbody>{env.map(([a, e]) => <tr key={a} className="border-b border-[#f1f4f8]"><td className="py-2 font-medium">{a}</td><td>{e.max_rows ?? "–"}</td><td>{e.max_amount ? rupees(e.max_amount * 100) : "–"}</td></tr>)}</tbody></table>
              <KV k="Protected actions (always need a human)" v={p.limits.protected.join(", ") || "none"} />
              <KV k="Two approvers at or above" v={p.limits.tiers.two_approvers_above_amount ? rupees(p.limits.tiers.two_approvers_above_amount * 100) : "tier T3 only"} />
              <KV k="Approval valid for" v={`${Math.round((p.limits.tiers.approval_ttl_seconds || 900) / 60)} minutes`} />
              <KV k="Shadow mode" v={p.limits.shadow_mode.on_hold ? "on, for untrusted-source holds" : "off"} />
            </div>
          )}
          {tab === "labels" && (
            <div className="grid md:grid-cols-2 gap-6 text-[13px]">
              <div><div className="h-label mb-2">Column labels</div>{Object.entries(p.labels.labels).map(([k, v]) => <KV key={k} k={k} v={v} />)}</div>
              <div><div className="h-label mb-2">Destinations (cleared up to)</div>{Object.entries(p.labels.destinations).map(([k, v]) => <KV key={k} k={k.replace(/_/g, " ")} v={v} />)}<p className="text-[12px] text-[#64748b] mt-3">Unlabelled columns default to INTERNAL. Catalog version {p.labels.catalog_version}.</p></div>
            </div>
          )}
          {tab === "budgets" && (
            <div className="text-[13px]">{Object.keys(p.budgets).length === 0 ? <p className="text-[#64748b]">This organisation has no cumulative budgets.</p> :
              Object.entries(p.budgets).map(([k, b]) => <KV key={k} k={k.replace(/_/g, " ")} v={`${b.action}: ${rupees(b.amount * 100)} per hour, keyed by ${b.key.join(" + ")}`} />)}</div>
          )}
        </section>
        <aside className="card p-5">
          <h2 className="font-semibold mb-2">Key details</h2>
          <KV k="Version" v={`v${p.version}`} /><KV k="Hash" v={<code>{p.hash.slice(0, 10)}…</code>} /><KV k="Updated" v={p.updated.replace("T", " ")} />
          <KV k="Labels" v={p.counts.labels} /><KV k="Envelopes" v={p.counts.envelopes} /><KV k="Budgets" v={p.counts.budgets} /><KV k="Agents" v={p.counts.agents} />
          <button className="btn w-full mt-4" onClick={onSwitchOrg}>Switch organisation</button>
        </aside>
      </div>
    </div>
  );
}
