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
        <button className="btn btn-primary" onClick={doVerify}>Verify chain</button>
        <button className="btn" onClick={load}>Refresh</button>
        {verify && (verify.ok ? <span className="text-[#56d364]">Chain intact</span> : <span className="text-[#ff7b72]">Chain broken at entry #{verify.first_broken_seq}</span>)}
      </div>
      <table className="w-full text-sm">
        <thead><tr className="text-left text-[#8b949e]"><th>#</th><th>time</th><th>who</th><th>what</th><th>decision</th><th>rule</th><th>path</th><th>hash</th><th></th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.seq} className={`border-t border-[#30363d] ${broken != null && r.seq >= broken ? "bg-[#f8514922]" : ""}`}>
              <td className="py-1">{r.seq}</td>
              <td>{new Date(r.ts * 1000).toLocaleTimeString()}</td>
              <td>{r.agent}</td><td>{r.action}</td>
              <td className={r.decision === "BLOCK" || r.decision === "VOID" ? "text-[#ff7b72]" : r.decision === "HOLD" ? "text-[#d29922]" : "text-[#56d364]"}>{r.decision}</td>
              <td>{r.rule}</td><td className="text-[#8b949e]">{r.decision_path}</td>
              <td className="font-mono text-xs text-[#8b949e]">{r.entry_hash.slice(0, 8)}</td>
              <td>
                <button className="btn" onClick={() => doReplay(r.seq)}>Replay</button>
                {replays[r.seq] && <span className="ml-2 text-xs">{replays[r.seq].error ? <span className="text-[#ff7b72]">{replays[r.seq].error}</span> : replays[r.seq].reproduced === true ? <span className="text-[#56d364]">Reproduced</span> : replays[r.seq].reproduced === false ? <span className="text-[#ff7b72]">MISMATCH</span> : <span className="text-[#8b949e]">n/a</span>}</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Overlay>
  );
}
