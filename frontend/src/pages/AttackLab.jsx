import { useEffect, useState } from "react";
import Overlay from "../components/Overlay";
import { call } from "../api";

const stopped = (o = "") => ["BLOCK", "HOLD", "REFUSED", "STRUCTURAL"].includes(o) || o.startsWith("VOID");
const cls = (o = "") => o === "" ? "" : o.startsWith("FAIL") ? "pill-block" : stopped(o) ? (o === "HOLD" ? "pill-hold" : o === "STRUCTURAL" ? "pill-info" : "pill-block") : "pill-allow";
const short = (o = "") => o.replace("VOID:", "VOID ").replace("_drift", "");

function AddCase({ onClose }) {
  const [c, setC] = useState({ domain: "bank", agent: "refund-agent", action: "refund", args: '{"customer":"C-1042","month":"March","match":"batch"}', user_instruction: "Refund C-1042's duplicate March charges" });
  const [out, setOut] = useState(null);
  const run = async () => { setOut({ wait: true }); try { setOut(await call("/lab/case", { method: "POST", body: { ...c, args: JSON.parse(c.args || "{}") } })); } catch (e) { setOut({ error: e.message }); } };
  return (
    <Overlay title="Add your own case" onClose={onClose} width={560} subtitle="Runs once in all three modes on freshly seeded data."
             footer={<div className="flex gap-2"><button className="btn btn-primary" onClick={run}>Run in all modes</button><button className="btn btn-quiet ml-auto" onClick={onClose}>Close</button></div>}>
      <div className="grid grid-cols-2 gap-3">
        {["domain", "agent", "action"].map((k) => <label key={k} className="text-[12px] text-[#64748b]">{k}<input className="field mt-1" value={c[k]} onChange={(e) => setC({ ...c, [k]: e.target.value })} /></label>)}
        <label className="text-[12px] text-[#64748b]">request (what the user said)<input className="field mt-1" value={c.user_instruction} onChange={(e) => setC({ ...c, user_instruction: e.target.value })} /></label>
        <label className="text-[12px] text-[#64748b] col-span-2">args (JSON)<input className="field mt-1 font-mono" value={c.args} onChange={(e) => setC({ ...c, args: e.target.value })} /></label>
      </div>
      {out && <div className="mt-4 text-[13px]">{out.wait ? "Running…" : out.error ? <span className="text-[#b91c1c]">{out.error}</span> : ["A", "B", "C"].map((m) => <span key={m} className="mr-5">Mode {m}: <span className={`pill ${cls(out[m])}`}>{short(out[m])}</span></span>)}</div>}
    </Overlay>
  );
}

// Numbers are shown exactly as the gateway returns them: nothing here is hard-coded.
export default function AttackLab() {
  const [suite, setSuite] = useState(null);
  const [res, setRes] = useState(null);
  const [running, setRunning] = useState(false);
  const [liveAi, setLiveAi] = useState(false);
  const [err, setErr] = useState("");
  const [add, setAdd] = useState(false);
  useEffect(() => { call("/lab/suite").then(setSuite).catch((e) => setErr(e.message)); call("/lab/last").then((r) => r.summary && setRes(r)).catch(() => {}); }, []);
  const run = async () => {
    setRunning(true); setErr("");
    try { setRes(await call(`/lab/run?mode=ALL&ai_checks=${liveAi}`, { method: "POST" })); } catch (e) { setErr(e.message); }
    setRunning(false);
  };
  const S = res?.summary;
  const n = suite?.cases?.length;
  const hash = res?.suite_commit || suite?.commit;
  const rows = res?.cases || (suite?.cases || []).map((c) => ({ id: c.id, title: c.title, domain: c.domain, expected: { C: c.expect_C }, A: {}, B: {}, C: {} }));

  return (
    <div className="p-6 space-y-5 h-full overflow-auto">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-[22px] font-semibold">Attack Lab</h1>
          <p className="text-[13px] text-[#64748b]">Evidence against baselines: {n ?? "…"} attacks, each with a harmless twin (the first 22 were pre-registered).</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-1.5 text-[12px] text-[#64748b]" title="Live model calls are slower and can change between runs. The default run uses the rules alone, so it is reproducible."><input type="checkbox" checked={liveAi} onChange={(e) => setLiveAi(e.target.checked)} />Include live AI checks</label>
          <button className="btn btn-primary" onClick={run} disabled={running}>{running ? "Running…" : "Run suite"}</button>
          <button className="btn" onClick={() => setAdd(true)}>Add own case</button>
        </div>
      </div>
      {err && <p className="text-[#b91c1c] text-[13px]">{err}</p>}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[["A", "Mode A", "allowlist + default deny"], ["B", "Mode B", "argument-bound approvals (normal gate)"], ["C", "Mode C", "SEALGATE"]].map(([m, t, sub]) => (
          <div key={m} className={`card p-5 ${m === "C" ? "!border-[#2563eb] ring-1 ring-[#2563eb]/20" : ""}`}>
            <div className="text-[13px] font-semibold">{t} <span className="font-normal text-[#64748b]">· {sub}</span></div>
            <div className="grid grid-cols-2 gap-4 mt-3">
              <div><div className="text-[28px] font-semibold leading-none">{S ? `${S[m].attacks_stopped} / ${S[m].attacks_total}` : "–"}</div><div className="text-[12px] text-[#64748b] mt-1">attacks stopped</div></div>
              <div><div className="text-[28px] font-semibold leading-none text-[#15803d]">{S ? `${S[m].benign_allowed} / ${S[m].benign_total}` : "–"}</div><div className="text-[12px] text-[#64748b] mt-1">harmless allowed</div></div>
            </div>
          </div>
        ))}
      </div>

      {res?.misses?.length > 0 && (
        <div className="card p-4 !border-[#fde68a] bg-[#fffbeb] text-[13px]">
          <b className="text-[#b45309]">Reported misses (exactly as produced)</b>
          <ul className="list-disc ml-5 mt-1 text-[#334155]">{res.misses.map((m, i) => <li key={i}>{m.id}: {m.title} — {m.what} (got {m.outcome}{m.expected ? `, expected ${m.expected}` : ""})</li>)}</ul>
        </div>
      )}

      <div className="card overflow-auto">
        <div className="px-5 py-3 font-semibold">Attack cases</div>
        <table className="w-full text-[13px]">
          <thead><tr className="text-left text-[11px] uppercase tracking-wider text-[#64748b] border-y border-[#e3e8ef] bg-[#fafbfd]"><th className="px-5 py-2">#</th><th>Attack</th><th>Domain</th><th>A</th><th>B (normal gate)</th><th>C (SEALGATE)</th><th>Harmless twin (C)</th><th className="pr-5">Result</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-b border-[#f1f4f8]">
                <td className="px-5 py-2.5 font-mono text-[12px]">{r.id}</td><td className="max-w-[300px]">{r.title}</td><td className="text-[#64748b] capitalize">{r.domain}</td>
                <td>{r.A?.attack && <span className={`pill ${cls(r.A.attack)}`}>{short(r.A.attack)}</span>}</td>
                <td>{r.B?.attack && <span className={`pill ${cls(r.B.attack)}`}>{short(r.B.attack)}</span>}</td>
                <td>{r.C?.attack ? <span className={`pill ${cls(r.C.attack)}`}>{short(r.C.attack)}</span> : <span className="text-[#94a3b8]">expect {short(r.expected?.C)}</span>}</td>
                <td>{r.C?.twin && <span className={`pill ${cls(r.C.twin)}`}>{short(r.C.twin)}</span>}</td>
                <td className="pr-5">{r.C?.attack && <span className={`pill ${stopped(r.C.attack) ? "pill-allow" : "pill-block"}`}>{stopped(r.C.attack) ? "Prevented" : "Missed"}</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-[12px] text-[#64748b]">Suite commit <code>{hash?.hash?.slice(0, 7) || "–"}</code>{hash?.time && ` · committed ${hash.time.slice(0, 16).replace("T", " ")}`}{res && ` · run ${res.ran_at} in ${res.seconds}s, AI checks ${res.ai === "live" ? "live" : "off"}`}. Known limits: {res?.known_limits?.join("; ") || "unmediated channels; paraphrased personal data is best-effort"}.</p>
      {add && <AddCase onClose={() => setAdd(false)} />}
    </div>
  );
}
