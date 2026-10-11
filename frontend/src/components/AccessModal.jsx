import { useState } from "react";
import Overlay from "./Overlay";
import { USERS } from "../api";
import { useUser } from "../hooks/useUser";

// An agent asking a person for access. Nothing has been sent to the safety gateway until this is granted.
export default function AccessModal({ a, queued, onGrant, onDeny, onLater }) {
  const [prompt, setPrompt] = useState(false);
  const me = useUser();
  const name = USERS.find((u) => u.id === me)?.name || me;
  return (
    <Overlay title={`${a.agent_name || a.agent} is asking for access`} onClose={onLater} width={600}
             badge={<span className="pill pill-info mr-1">ACCESS REQUEST</span>}
             subtitle={queued > 0 ? `${queued} more waiting after this one` : "The agent will not do anything until you decide."}
             footer={(
               <div className="flex flex-wrap items-center gap-2">
                 <button className="btn btn-primary" onClick={() => onGrant(a.id)}>Grant access as {name}</button>
                 <button className="btn btn-danger" onClick={() => onDeny(a.id)}>Deny</button>
                 <button className="btn btn-quiet ml-auto" onClick={onLater}>Decide later</button>
               </div>
             )}>
      <div className="space-y-3 text-[13px]">
        <p>It wants to run <b className="font-mono text-[12px]">{a.tool}</b>{a.intent ? <> because: “{a.intent}”</> : null}.</p>
        <div>
          <div className="h-label mb-1">What it would send to the gateway</div>
          <pre className="bg-[#f8fafc] border border-[#e3e8ef] rounded-lg px-3 py-2 text-[12px] overflow-auto">{JSON.stringify(a.args, null, 2)}</pre>
        </div>
        <p className="text-[#64748b]">If you grant access, the agent signs this proposal and sends it. The gateway then measures it on a copy of the data, and a person still has to approve the result before anything changes.</p>
        <button className="text-[12px] text-[#2563eb] underline" onClick={() => setPrompt(!prompt)}>{prompt ? "Hide" : "Show"} this agent's prompt</button>
        {prompt && <pre className="bg-[#f8fafc] border border-[#e3e8ef] rounded-lg p-3 text-[12px] whitespace-pre-wrap max-h-[220px] overflow-auto">{a.prompt}</pre>}
      </div>
    </Overlay>
  );
}
