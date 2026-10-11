import { useEffect, useRef, useState } from "react";
import Icon from "./Icon";
import { SAMPLE_PROMPTS, tidy } from "../api";

// Just the conversation and the prompt box. What the agent is doing step by step lives on the Agent Activity page.
export default function ChatDrawer({ domain, messages, working, onSend, onClose, mode, draft, setDraft, onWatch }) {
  const [attach, setAttach] = useState("");
  const [showAttach, setShowAttach] = useState(false);
  const [samples, setSamples] = useState(false);
  const end = useRef(null);
  useEffect(() => { end.current?.scrollIntoView({ block: "end" }); }, [messages, working]);
  useEffect(() => { const h = (e) => e.key === "Escape" && onClose(); window.addEventListener("keydown", h); return () => window.removeEventListener("keydown", h); }, [onClose]);
  const send = () => { const t = draft.trim(); if (!t) return; setDraft(""); onSend(t, attach); setAttach(""); setShowAttach(false); setSamples(false); };

  return (
    <div className="fixed inset-0 z-40" onClick={onClose}>
      <aside className="drawer-in absolute right-0 top-0 h-full w-[500px] max-w-full bg-white border-l border-[#e3e8ef] shadow-2xl flex flex-col" onClick={(e) => e.stopPropagation()} aria-label="Ask an agent">
        <div className="h-14 shrink-0 px-5 flex items-center justify-between border-b border-[#e3e8ef]">
          <div className="font-semibold flex items-center gap-2"><Icon name="chat" size={16} />Chat</div>
          <div className="flex items-center gap-3 text-[12px] text-[#64748b]">
            <span>{mode?.llm_configured ? `${(mode.providers || [])[0]}` : <b className="text-[#b91c1c]">No language model</b>}</span>
            <button onClick={onClose} className="p-1 rounded-md hover:bg-[#f1f5f9]" aria-label="Close"><Icon name="x" /></button>
          </div>
        </div>

        <div className="flex-1 overflow-auto px-5 py-4 space-y-3" role="log" aria-live="polite">
          {messages.length === 0 && <p className="text-[13px] text-[#64748b]">Ask a question or ask for an operation. When an agent wants to act, a window asks you to grant it access first.</p>}
          {messages.map((m, i) => m.from === "note" ? <div key={i} className="text-[12px] text-[#64748b] text-center">{m.text}</div>
            : m.from === "gate" ? <div key={i} className="border-l-2 border-[#2563eb] pl-3 py-0.5 text-[13px]"><div className="h-label text-[#2563eb]">SEALGATE</div>{tidy(m.text)}</div>
            : m.from === "user" ? <div key={i} className="flex justify-end"><div className="max-w-[88%] rounded-xl bg-[#2563eb] text-white px-3 py-2 text-[13px] whitespace-pre-wrap">{m.text}{m.attachment && <div className="mt-1 text-[11px] opacity-80">+ attached document ({m.attachment.length.toLocaleString("en-IN")} characters)</div>}</div></div>
            : <div key={i} className="text-[13px]"><div className="h-label">{m.agent || "Assistant"}</div><span className="whitespace-pre-wrap">{m.text}</span></div>)}
          {working && <div className="text-[13px] text-[#64748b] flex items-center gap-2" role="status"><span className="inline-block w-2 h-2 rounded-full bg-[#2563eb] animate-pulse" />Working… <button className="text-[#2563eb] underline" onClick={onWatch}>watch it step by step</button></div>}
          <div ref={end} />
        </div>

        <div className="border-t border-[#e3e8ef] p-4 space-y-2">
          {samples && (
            <div className="rounded-lg border border-[#e3e8ef] max-h-[300px] overflow-auto p-2 space-y-2 bg-[#fafbfd]">
              {(SAMPLE_PROMPTS[domain] || []).map(([title, items]) => (
                <div key={title}>
                  <div className="h-label px-2">{title}</div>
                  {items.map((p) => <button key={p} className="w-full text-left px-2 py-1.5 rounded-md hover:bg-white text-[12.5px] leading-snug text-[#334155]" onClick={() => { setDraft(p); setSamples(false); }}>{p}</button>)}
                </div>
              ))}
            </div>
          )}
          {showAttach && <textarea className="field font-mono !text-[12px]" rows={4} placeholder="Paste an email, ticket or document the agent should read along with your request" value={attach} onChange={(e) => setAttach(e.target.value)} aria-label="Attached document" />}
          <textarea className="field" rows={3} aria-label="Request to the agent" placeholder="Ask anything, or ask an agent to do something" value={draft} onChange={(e) => setDraft(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }} />
          <div className="flex gap-2">
            <button className="btn" onClick={() => setSamples(!samples)}>Sample prompts</button>
            <button className="btn" onClick={() => setShowAttach(!showAttach)}>{showAttach ? "No document" : "Attach document"}</button>
            <button className="btn btn-primary ml-auto" onClick={send} disabled={!draft.trim()}>Send</button>
          </div>
        </div>
      </aside>
    </div>
  );
}
