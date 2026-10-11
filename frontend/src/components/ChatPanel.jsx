import { useEffect, useRef, useState } from "react";
import { call, tidy } from "../api";

const SCENARIOS = {
  bank: [
    ["bank-update-phone", "Update a phone number", "An ordinary one-record change goes straight through."],
    ["bank-refund", "Refund one customer's duplicates", "The agent asks for one customer; the sandbox shows 61."],
    ["bank-payee-poisoned", "Change a vendor's bank account from an email", "Untrusted source: the agent continues in a sandbox."],
    ["bank-batch-transfer", "Pay the 40 pending invoices", "Needs two approvers; then try changing the data before executing."],
  ],
  hospital: [["hospital-report", "Share one patient's report with a doctor", "The attachment quietly holds 340 patients."]],
  shop: [
    ["shop-relay", "Send the customer list to an agency", "One agent saves a file, another emails it out."],
    ["shop-newsletter", "Send the October newsletter", "Harmless mail is allowed."],
  ],
};

export default function ChatPanel({ domain, messages }) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const end = useRef(null);
  useEffect(() => { end.current?.scrollIntoView({ block: "end" }); }, [messages]);
  const send = async () => {
    const t = text.trim(); if (!t || busy) return; setText(""); setBusy(true);
    try { await call("/demo/chat", { method: "POST", body: { text: t } }); } catch { /* the offline banner covers this */ }
    setBusy(false);
  };
  const run = (name) => call(`/demo/${name}`, { method: "POST" }).catch(() => {});

  return (
    <section className="flex flex-col h-full min-h-0 border-r border-[#d0d7de]" aria-label="Conversation">
      <div className="px-4 py-2 label border-b border-[#d0d7de]">Conversation with the agent</div>
      <div className="flex-1 overflow-auto px-4 py-4 space-y-3" role="log" aria-live="polite">
        {messages.length === 0 && <p className="text-[#59636e] text-[13px]">Nothing yet. Choose a scenario below, or type a request such as “Refund C-1042's duplicate March charges”.</p>}
        {messages.map((m, i) => m.from === "gate" ? (
          <div key={i} className="border-l-2 border-[#0969da] pl-3 py-0.5 text-[13px]">
            <div className="label text-[#0969da]">SEALGATE</div>{tidy(m.text)}
          </div>
        ) : m.from === "user" ? (
          <div key={i} className="flex justify-end"><div className="max-w-[85%] rounded-lg bg-[#0969da33] border border-[#0969da66] px-3 py-1.5 text-[13px]">{m.text}</div></div>
        ) : (
          <div key={i} className="text-[13px]"><div className="label">{m.agent || "Agent"}</div>{m.text}</div>
        ))}
        <div ref={end} />
      </div>
      <div className="border-t border-[#d0d7de] p-3 space-y-2">
        <details open={messages.length === 0}>
          <summary className="label cursor-pointer hover:text-[#3d444d]">Scenarios</summary>
          <ul className="mt-2 space-y-1">
            {(SCENARIOS[domain] || []).map(([name, title, hint]) => (
              <li key={name}>
                <button className="w-full text-left px-2.5 py-1.5 rounded-md hover:bg-[#f3f4f6] border border-transparent hover:border-[#d0d7de]" onClick={() => run(name)}>
                  <div className="text-[13px] font-medium">{title}</div><div className="text-[12px] text-[#59636e]">{hint}</div>
                </button>
              </li>
            ))}
          </ul>
        </details>
        <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); send(); }}>
          <input className="flex-1 bg-[#ffffff] border border-[#d0d7de] rounded-md px-3 py-2 text-[13px] placeholder:text-[#6e7781]" aria-label="Request to the agent"
                 placeholder="Ask the agent to do something" value={text} onChange={(e) => setText(e.target.value)} />
          <button className="btn btn-primary" type="submit" disabled={busy || !text.trim()}>Send</button>
        </form>
        <p className="text-[11px] text-[#6e7781]">Approvals and execution happen in the console on the right.</p>
      </div>
    </section>
  );
}
