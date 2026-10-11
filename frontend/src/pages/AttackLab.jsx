import { useEffect, useState } from "react";
import { call } from "../api";

const color = (o = "") => o.startsWith("VOID") || o === "BLOCK" || o === "REFUSED" ? "text-[#cf222e]" : o === "HOLD" ? "text-[#9a6700]" : o === "STRUCTURAL" ? "text-[#0969da]" : o.startsWith("FAIL") ? "text-[#cf222e]" : "text-[#1a7f37]";

// Numbers are shown exactly as the gateway returns them: nothing here is hard-coded.
export default function AttackLab() {
  const [suite, setSuite] = useState(null);
  const [res, setRes] = useState(null);
  const [running, setRunning] = useState(false);
  const [err, setErr] = useState("");
  const [custom, setCustom] = useState({ domain: "bank", agent: "refund-agent", action: "refund", args: '{"customer":"C-1042","month":"March","match":"batch"}', user_instruction: "Refund C-1042's duplicate March charges" });
  const [customOut, setCustomOut] = useState(null);

  useEffect(() => { call("/lab/suite").then(setSuite).catch((e) => setErr(e.message)); call("/lab/last").then((r) => r.summary && setRes(r)).catch(() => {}); }, []);

  const run = async () => {
    setRunning(true); setErr("");
    try { setRes(await call("/lab/run?mode=ALL", { method: "POST" })); } catch (e) { setErr(e.message); }
    setRunning(false);
  };
  const addCase = async () => {
    try { setCustomOut(await call("/lab/case", { method: "POST", body: { ...custom, args: JSON.parse(custom.args || "{}") } })); }
    catch (e) { setCustomOut({ error: e.message }); }
  };
  const S = res?.summary;
  const hash = res?.suite_commit || suite?.commit;

  return (
    <div className="p-6 overflow-auto h-full">
      <div className="flex items-center gap-4 mb-4">
        <h1 className="text-lg font-semibold">Attack lab</h1>
        <span className="text-sm text-[#59636e]">suite commit <code className="text-[#0969da]">{hash?.hash?.slice(0, 7) || "—"}</code> {hash?.time && `(${hash.time.slice(0, 16).replace("T", " ")})`} · {suite?.cases?.length ?? "…"} attack/twin pairs (the first 22 were pre-registered; later additions are logged)</span>
        <button className="btn btn-primary ml-auto" onClick={run} disabled={running}>{running ? "Running (about 30 seconds)" : "Run suite"}</button>
      </div>
      {err && <p className="text-[#cf222e] mb-3">{err}</p>}

      <div className="grid grid-cols-3 gap-4 mb-6">
        {[["A", "allowlist + default deny"], ["B", "argument-bound approvals"], ["C", "SEALGATE"]].map(([m, label]) => (
          <div key={m} className={`panel p-4 ${m === "C" ? "!border-[#0969da]" : ""}`}>
            <div className="text-sm text-[#59636e]">Mode {m}: {label}</div>
            <div className="text-3xl font-semibold mt-2">{S ? `${S[m].attacks_stopped} / ${S[m].attacks_total}` : "—"}<span className="text-sm text-[#59636e] font-normal"> attacks stopped</span></div>
            <div className="text-base mt-1 text-[#1a7f37]">{S ? `${S[m].benign_allowed} / ${S[m].benign_total}` : "—"}<span className="text-sm text-[#59636e]"> harmless allowed</span></div>
          </div>
        ))}
      </div>

      {res && <p className="text-sm text-[#59636e] mb-2">Run at {res.ran_at} in {res.seconds}s. Known limits: {res.known_limits.join(" · ")}.</p>}
      {res?.misses?.length > 0 && (
        <div className="panel p-3 mb-4 text-[13px] !border-[#9a670066]">
          <b className="text-[#9a6700]">Reported misses (exactly as produced)</b>
          <ul className="list-disc ml-5 mt-1">{res.misses.map((m, i) => <li key={i}>{m.id} — {m.title}: {m.what} (got {m.outcome}{m.expected ? `, expected ${m.expected}` : ""})</li>)}</ul>
        </div>
      )}

      <table className="w-full text-sm mb-8">
        <thead><tr className="text-left text-[#59636e]"><th className="py-1">Attack</th><th>A</th><th>B</th><th>C</th><th>expected C</th><th>Benign twin (C)</th></tr></thead>
        <tbody>
          {(res?.cases || suite?.cases?.map((c) => ({ id: c.id, title: c.title, domain: c.domain, expected: { C: c.expect_C }, A: {}, B: {}, C: {} })) || []).map((r) => (
            <tr key={r.id} className="border-t border-[#d0d7de]">
              <td className="py-1">{r.id} · {r.title} <span className="text-[#59636e]">({r.domain})</span></td>
              <td className={color(r.A?.attack)}>{r.A?.attack || ""}</td>
              <td className={color(r.B?.attack)}>{r.B?.attack || ""}</td>
              <td className={`${color(r.C?.attack)} font-semibold`}>{r.C?.attack || ""}</td>
              <td className="text-[#59636e]">{r.expected?.C}</td>
              <td className={color(r.C?.twin)}>{r.C?.twin || ""}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2 className="font-semibold mb-2">Add your own case</h2>
      <div className="grid grid-cols-2 gap-2 max-w-3xl mb-2">
        {["domain", "agent", "action", "user_instruction"].map((k) => (
          <label key={k} className="text-xs text-[#59636e]">{k}<input className="w-full bg-[#ffffff] border border-[#d0d7de] rounded-md px-2 py-1 text-[#1f2328]" value={custom[k]} onChange={(e) => setCustom({ ...custom, [k]: e.target.value })} /></label>
        ))}
        <label className="text-xs text-[#59636e] col-span-2">args (JSON)<input className="w-full bg-[#ffffff] border border-[#d0d7de] rounded-md px-2 py-1 text-[#1f2328] font-mono" value={custom.args} onChange={(e) => setCustom({ ...custom, args: e.target.value })} /></label>
      </div>
      <button className="btn btn-primary" onClick={addCase}>Run in all modes</button>
      {customOut && <div className="mt-2 text-sm">{customOut.error ? <span className="text-[#cf222e]">{customOut.error}</span> : ["A", "B", "C"].map((m) => <span key={m} className="mr-4">Mode {m}: <b className={color(customOut[m])}>{customOut[m]}</b></span>)}</div>}
    </div>
  );
}
