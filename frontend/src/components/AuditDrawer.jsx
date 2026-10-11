import { useEffect, useState } from "react";
import Overlay from "./Overlay";
import { call } from "../api";

export default function AuditDrawer({ onClose }) {
  const [rows, setRows] = useState([]);
  const [verify, setVerify] = useState(null);
  const [replays, setReplays] = useState({});
  const load = () => call("/audit?limit=60").then((r) => setRows(r.slice().reverse())).catch(() => {});
  useEffect(() => { load(); }, []);
  const doVerify = async () => setVerify(await call("/audit/verify", { method: "POST" }));
  const doReplay = async (seq) => {
    try { setReplays({ ...replays, [seq]: await call(`/audit/replay/${seq}`, { method: "POST" }) }); }
    catch (e) { setReplays({ ...replays, [seq]: { error: e.message } }); }
  };
  const broken = verify && !verify.ok ? verify.first_broken_seq : null;

  return (
    <Overlay title="Audit log · hash chain" onClose={onClose} wide>
      <div className="flex items-center gap-3 mb-4">
        <button className="btn btn-accent" onClick={doVerify}>Verify chain</button>
        <button className="btn" onClick={load}>Refresh</button>
        {verify && (verify.ok ? <span className="text-emerald-400">✓ chain intact</span> : <span className="text-rose-400">✗ chain broken at entry #{verify.first_broken_seq}</span>)}
      </div>
      <table className="w-full text-sm">
        <thead><tr className="text-left text-slate-500"><th>#</th><th>time</th><th>who</th><th>what</th><th>decision</th><th>rule</th><th>path</th><th>hash</th><th></th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.seq} className={`border-t border-slate-800 ${broken != null && r.seq >= broken ? "bg-rose-950/40" : ""}`}>
              <td className="py-1">{r.seq}</td>
              <td>{new Date(r.ts * 1000).toLocaleTimeString()}</td>
              <td>{r.agent}</td><td>{r.action}</td>
              <td className={r.decision === "BLOCK" || r.decision === "VOID" ? "text-rose-300" : r.decision === "HOLD" ? "text-amber-300" : "text-emerald-300"}>{r.decision}</td>
              <td>{r.rule}</td><td className="text-slate-400">{r.decision_path}</td>
              <td className="font-mono text-xs text-slate-500">{r.entry_hash.slice(0, 8)}</td>
              <td>
                <button className="btn" onClick={() => doReplay(r.seq)}>Replay</button>
                {replays[r.seq] && <span className="ml-2 text-xs">{replays[r.seq].error ? <span className="text-rose-300">{replays[r.seq].error}</span> : replays[r.seq].reproduced === true ? <span className="text-emerald-300">Reproduced ✓</span> : replays[r.seq].reproduced === false ? <span className="text-rose-300">MISMATCH</span> : <span className="text-slate-400">n/a</span>}</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Overlay>
  );
}
