import { useEffect, useRef, useState } from "react";
import Icon from "./Icon";
import ActivityFeed from "./ActivityFeed";
import PromptsView from "./PromptsView";
import { tidy } from "../api";

const SCENARIOS = {
  bank: [
    ["bank-update-phone", "Update a phone number", "An ordinary one-record change goes straight through."],
    ["bank-refund", "Refund one customer's duplicates", "Scripted: the agent claims one customer but asks for the whole batch."],
    ["bank-payee-poisoned", "Change a vendor's bank account from an email", "Untrusted source: the agent continues in a sandbox."],
    ["bank-batch-transfer", "Pay the 40 pending invoices", "Needs two approvers; change the data before executing."],
  ],
  hospital: [["hospital-report", "Share one patient's report with a doctor", "Scripted: the attachment quietly holds 340 patients."]],
  shop: [
    ["shop-relay", "Send the customer list to an agency", "One agent saves a file, another emails it out."],
    ["shop-newsletter", "Send the October newsletter", "Harmless mail is allowed."],
  ],
};
const HINT = {
  bank: "Refund C-1042's duplicate March charges, or: what happens if an agent refunds more than I asked?",
  hospital: "Share P-0001's report with dr.shah@punecare.example",
  shop: "Send the October newsletter",
};

export default function ChatDrawer({ domain, messages, working, onSend, onRun, onClose, activity, mode, onMode, tab, setTab }) {
  const [text, setText] = useState("");
  const end = useRef(null);
  useEffect(() => { end.current?.scrollIntoView({ block: "end" }); }, [messages, working, tab]);
  useEffect(() => { const h = (e) => e.key === "Escape" && onClose(); window.addEventListener("keydown", h); return () => window.removeEventListener("keydown", h); }, [onClose]);
  const send = () => { const t = text.trim(); if (!t) return; setText(""); onSend(t); };
  const live = mode?.mode === "llm";

  return (
    <div className="fixed inset-0 z-40" onClick={onClose}>
      <aside className="drawer-in absolute right-0 top-0 h-full w-[640px] max-w-full bg-white border-l border-[#e3e8ef] shadow-2xl flex flex-col" onClick={(e) => e.stopPropagation()} aria-label="Ask an agent">
        <div className="h-14 shrink-0 px-5 flex items-center justify-between border-b border-[#e3e8ef]">
          <div className="font-semibold flex items-center gap-2"><Icon name="chat" size={16} />Agent</div>
          <div className="flex items-center gap-3">
            <div className="flex rounded-lg border border-[#d5dbe5] overflow-hidden text-[12px]" role="group" aria-label="Agent mode">
              {[["llm", "Live LLM"], ["scripted", "Scripted demo"]].map(([m, l]) => (
                <button key={m} onClick={() => onMode(m)} aria-pressed={mode?.mode === m} disabled={m === "llm" && !mode?.llm_configured}
                        title={m === "llm" ? (mode?.llm_configured ? `${mode.provider} · ${mode.model}` : "No language model configured (set AI_PROVIDER, AI_MODEL, AI_API_KEY)") : "Fixed scripts with a deliberately mis-scoped agent"}
                        className={`px-2.5 py-1 ${mode?.mode === m ? "bg-[#2563eb] text-white" : "bg-white text-[#475569] hover:bg-[#f8fafc]"} disabled:opacity-40`}>{l}</button>
              ))}
            </div>
            <button onClick={onClose} className="p-1 rounded-md text-[#64748b] hover:bg-[#f1f5f9]" aria-label="Close"><Icon name="x" /></button>
          </div>
        </div>
        <div className="shrink-0 px-5 pt-2 flex gap-6 border-b border-[#e3e8ef]" role="tablist">
          {[["chat", "Chat"], ["activity", `Live activity${activity.length ? ` (${activity.length})` : ""}`], ["prompts", "Prompts"]].map(([id, l]) => (
            <button key={id} role="tab" aria-selected={tab === id} className={`tab ${tab === id ? "tab-active" : ""}`} onClick={() => setTab(id)}>{l}</button>
          ))}
        </div>

        {tab === "chat" && (
          <div className="flex-1 overflow-auto px-5 py-4 space-y-3" role="log" aria-live="polite">
            <p className="text-[12px] text-[#64748b]">{live ? `Every message goes to the language model (${mode.provider} · ${mode.model}). It can answer questions or call tools; the gateway checks every tool call.` : "Scripted mode: requests are matched to fixed routines. Switch to Live LLM to ask anything."}</p>
            {messages.length === 0 && <p className="text-[13px] text-[#64748b]">Nothing yet. Try “{HINT[domain]}”.</p>}
            {messages.map((m, i) => m.from === "gate" ? (
              <div key={i} className="border-l-2 border-[#2563eb] pl-3 py-0.5 text-[13px]"><div className="h-label text-[#2563eb]">SEALGATE</div>{tidy(m.text)}</div>
            ) : m.from === "user" ? (
              <div key={i} className="flex justify-end"><div className="max-w-[85%] rounded-xl bg-[#2563eb] text-white px-3 py-2 text-[13px]">{m.text}</div></div>
            ) : (
              <div key={i} className="text-[13px]"><div className="h-label">{m.agent || "Agent"}</div><span className="whitespace-pre-wrap">{m.text}</span></div>
            ))}
            {working && <div className="text-[13px] text-[#64748b] flex items-center gap-2" role="status"><span className="inline-block w-2 h-2 rounded-full bg-[#2563eb] animate-pulse" />Agent is working… <button className="text-[#2563eb] underline" onClick={() => setTab("activity")}>watch live</button></div>}
            <div ref={end} />
          </div>
        )}
        {tab === "activity" && <ActivityFeed events={activity} working={working} />}
        {tab === "prompts" && <PromptsView events={activity} />}

        <div className="border-t border-[#e3e8ef] p-4 space-y-3">
          <details open={messages.length === 0 && tab === "chat"}>
            <summary className="h-label cursor-pointer">Scripted scenarios</summary>
            <ul className="mt-2 space-y-1">
              {(SCENARIOS[domain] || []).map(([name, title, hint]) => (
                <li key={name}><button aria-label={title} className="w-full text-left px-3 py-2 rounded-lg hover:bg-[#f1f5f9]" onClick={() => { setTab("activity"); onRun(name); }}>
                  <div className="text-[13px] font-medium">{title}</div><div className="text-[12px] text-[#64748b]">{hint}</div></button></li>
              ))}
            </ul>
          </details>
          <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); send(); }}>
            <input className="field flex-1" aria-label="Request to the agent" placeholder="Ask anything, or ask the agent to do something" value={text} onChange={(e) => setText(e.target.value)} />
            <button className="btn btn-primary" type="submit" disabled={!text.trim()}>Send</button>
          </form>
        </div>
      </aside>
    </div>
  );
}
