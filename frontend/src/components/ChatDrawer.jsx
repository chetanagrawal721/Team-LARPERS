import { useEffect, useRef, useState } from "react";
import Icon from "./Icon";
import ActivityFeed from "./ActivityFeed";
import PromptsView from "./PromptsView";
import { SAMPLE_PROMPTS, getUser, tidy } from "../api";

// An agent asking a person for access before it may even send its proposal to the gateway.
function AccessCard({ a, onGrant, onDeny }) {
  const [show, setShow] = useState(false);
  const pending = a.status === "pending";
  return (
    <div className={`rounded-xl border p-3.5 text-[13px] ${pending ? "border-[#bcd2ff] bg-[#f3f7ff]" : a.status === "granted" ? "border-[#bbf7d0] bg-[#f6fef9]" : "border-[#fecaca] bg-[#fff8f8]"}`}>
      <div className="flex items-center justify-between gap-2">
        <div className="font-semibold">{a.agent_name || a.agent} is asking for access</div>
        <span className={`pill ${pending ? "pill-info" : a.status === "granted" ? "pill-allow" : "pill-block"}`}>{pending ? "WAITING FOR YOU" : a.status.toUpperCase()}</span>
      </div>
      <p className="mt-1">"I want to run <b>{a.tool}</b>{a.intent ? <> because: {a.intent}</> : null}"</p>
      <pre className="mt-2 bg-white border border-[#e3e8ef] rounded-lg px-2.5 py-1.5 text-[12px] overflow-auto">{JSON.stringify(a.args, null, 2)}</pre>
      <p className="mt-2 text-[12px] text-[#64748b]">Nothing has been sent to the safety gateway yet. If you grant access, the agent signs and sends this proposal, the gateway measures it in a sandbox, and a person still has to approve the result.</p>
      <div className="mt-2 flex items-center gap-2">
        {pending && <><button className="btn btn-primary !py-1.5" onClick={() => onGrant(a.id)}>Grant access as {getUser().name}</button><button className="btn btn-danger !py-1.5" onClick={() => onDeny(a.id)}>Deny</button></>}
        {!pending && <span className="text-[12px] text-[#64748b]">{a.status} by {a.by}</span>}
        <button className="btn btn-quiet !py-1 ml-auto text-[12px]" onClick={() => setShow(!show)}>{show ? "Hide" : "View"} agent prompt</button>
      </div>
      {show && <pre className="mt-2 bg-white border border-[#e3e8ef] rounded-lg p-2.5 text-[12px] whitespace-pre-wrap max-h-[220px] overflow-auto">{a.prompt}</pre>}
    </div>
  );
}

function Samples({ domain, onPick }) {
  const groups = SAMPLE_PROMPTS[domain] || [];
  return (
    <details className="text-[13px]" open>
      <summary className="h-label cursor-pointer">Try these prompts</summary>
      <div className="mt-2 space-y-2 max-h-[190px] overflow-auto pr-1">
        {groups.map(([title, items]) => (
          <div key={title}>
            <div className="text-[11px] font-semibold text-[#64748b] mb-0.5">{title}</div>
            <ul className="space-y-0.5">{items.map((p) => <li key={p}><button className="w-full text-left px-2 py-1 rounded-md hover:bg-[#f1f5f9] text-[#334155]" onClick={() => onPick(p)}>{p}</button></li>)}</ul>
          </div>
        ))}
      </div>
    </details>
  );
}

export default function ChatDrawer({ domain, messages, working, onSend, onClose, activity, mode, tab, setTab, access, onGrant, onDeny, draft, setDraft }) {
  const [attach, setAttach] = useState("");
  const [showAttach, setShowAttach] = useState(false);
  const end = useRef(null);
  useEffect(() => { end.current?.scrollIntoView({ block: "end" }); }, [messages, working, tab, access.length]);
  useEffect(() => { const h = (e) => e.key === "Escape" && onClose(); window.addEventListener("keydown", h); return () => window.removeEventListener("keydown", h); }, [onClose]);
  const send = () => { const t = draft.trim(); if (!t) return; setDraft(""); onSend(t, attach); setAttach(""); setShowAttach(false); };
  const waiting = access.filter((a) => a.status === "pending").length;

  // chat messages and access requests, in the order they arrived
  const timeline = [...messages.map((m) => ({ ...m, t: m.t || 0, kind: "msg" })), ...access.map((a) => ({ a, t: a.ts, kind: "access" }))].sort((x, y) => x.t - y.t);

  return (
    <div className="fixed inset-0 z-40" onClick={onClose}>
      <aside className="drawer-in absolute right-0 top-0 h-full w-[660px] max-w-full bg-white border-l border-[#e3e8ef] shadow-2xl flex flex-col" onClick={(e) => e.stopPropagation()} aria-label="Ask an agent">
        <div className="h-14 shrink-0 px-5 flex items-center justify-between border-b border-[#e3e8ef]">
          <div className="font-semibold flex items-center gap-2"><Icon name="chat" size={16} />Agent chat</div>
          <div className="flex items-center gap-3 text-[12px] text-[#64748b]">
            <span title="Every request goes to a language model; nothing is scripted.">{mode?.llm_configured ? `Live LLM · ${(mode.providers || []).join(" → ")}` : <b className="text-[#b91c1c]">No language model available</b>}</span>
            <button onClick={onClose} className="p-1 rounded-md hover:bg-[#f1f5f9]" aria-label="Close"><Icon name="x" /></button>
          </div>
        </div>
        <div className="shrink-0 px-5 pt-2 flex gap-6 border-b border-[#e3e8ef]" role="tablist">
          {[["chat", `Chat${waiting ? ` (${waiting} waiting)` : ""}`], ["activity", `Live activity${activity.length ? ` (${activity.length})` : ""}`], ["prompts", "Prompts"]].map(([id, l]) => (
            <button key={id} role="tab" aria-selected={tab === id} className={`tab ${tab === id ? "tab-active" : ""}`} onClick={() => setTab(id)}>{l}</button>
          ))}
        </div>

        {tab === "chat" && (
          <div className="flex-1 overflow-auto px-5 py-4 space-y-3" role="log" aria-live="polite">
            {timeline.length === 0 && <p className="text-[13px] text-[#64748b]">Nothing yet. Ask a question, or ask for an operation. When an agent wants to act it will ask you for access here first.</p>}
            {timeline.map((m, i) => m.kind === "access" ? <AccessCard key={m.a.id} a={m.a} onGrant={onGrant} onDeny={onDeny} />
              : m.from === "gate" ? <div key={i} className="border-l-2 border-[#2563eb] pl-3 py-0.5 text-[13px]"><div className="h-label text-[#2563eb]">SEALGATE</div>{tidy(m.text)}</div>
              : m.from === "user" ? <div key={i} className="flex justify-end"><div className="max-w-[85%] rounded-xl bg-[#2563eb] text-white px-3 py-2 text-[13px] whitespace-pre-wrap">{m.text}{m.attachment && <div className="mt-1 text-[11px] opacity-80">+ attached document ({m.attachment.length} characters)</div>}</div></div>
              : <div key={i} className="text-[13px]"><div className="h-label">{m.agent || "Agent"}</div><span className="whitespace-pre-wrap">{m.text}</span></div>)}
            {working && <div className="text-[13px] text-[#64748b] flex items-center gap-2" role="status"><span className="inline-block w-2 h-2 rounded-full bg-[#2563eb] animate-pulse" />Working… <button className="text-[#2563eb] underline" onClick={() => setTab("activity")}>watch live</button></div>}
            <div ref={end} />
          </div>
        )}
        {tab === "activity" && <ActivityFeed events={activity} working={working} />}
        {tab === "prompts" && <PromptsView events={activity} />}

        <div className="border-t border-[#e3e8ef] p-4 space-y-3">
          {tab === "chat" && <Samples domain={domain} onPick={(p) => setDraft(p)} />}
          {showAttach && <textarea className="field font-mono !text-[12px]" rows={5} placeholder="Paste an email, ticket or document the agent should read along with your request" value={attach} onChange={(e) => setAttach(e.target.value)} aria-label="Attached document" />}
          <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); send(); }}>
            <input className="field flex-1" aria-label="Request to the agent" placeholder="Ask anything, or ask an agent to do something" value={draft} onChange={(e) => setDraft(e.target.value)} />
            <button type="button" className="btn" onClick={() => setShowAttach(!showAttach)} title="Attach a document">{showAttach ? "No document" : "Attach"}</button>
            <button className="btn btn-primary" type="submit" disabled={!draft.trim()}>Send</button>
          </form>
        </div>
      </aside>
    </div>
  );
}
