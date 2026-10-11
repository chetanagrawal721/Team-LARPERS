import { useEffect, useRef, useState } from "react";
import { call } from "../api";

const SCENARIOS = {
  bank: [["Update phone", "bank-update-phone"], ["Refund C-1042", "bank-refund"], ["Vendor email change", "bank-payee-poisoned"], ["Pay 40 invoices", "bank-batch-transfer"]],
  hospital: [["Share Ramesh's report", "hospital-report"]],
  shop: [["Customer list → agency", "shop-relay"], ["Newsletter", "shop-newsletter"]],
};

export default function ChatPanel({ domain, messages }) {
  const [text, setText] = useState("");
  const end = useRef(null);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);
  const send = async () => {
    const t = text.trim(); if (!t) return; setText("");
    try { await call("/demo/chat", { method: "POST", body: { text: t } }); } catch { /* shown by banner */ }
  };
  const run = (name) => call(`/demo/${name}`, { method: "POST" }).catch(() => {});

  return (
    <section className="flex flex-col h-full border-r border-slate-800">
      <div className="px-4 py-2 text-xs uppercase tracking-wide text-slate-400 border-b border-slate-800">User ↔ Agent</div>
      <div className="flex-1 overflow-auto p-4 space-y-3">
        {messages.length === 0 && <p className="text-slate-500">Pick a story below or type a request, e.g. “Refund C-1042's duplicate March charges”.</p>}
        {messages.map((m, i) => (
          m.from === "gate" ? (
            <div key={i} className="rounded-lg border border-cyan-500/40 bg-cyan-950/30 p-3 text-sm"><span className="text-cyan-300 font-semibold">🔏 SEALGATE</span> {m.text}</div>
          ) : (
            <div key={i} className={`flex ${m.from === "user" ? "justify-end" : ""}`}>
              <div className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm ${m.from === "user" ? "bg-slate-700" : "bg-slate-900 border border-slate-800"}`}>
                {m.from === "user" ? "👤 " : "🤖 "}{m.text}
              </div>
            </div>
          )
        ))}
        <div ref={end} />
      </div>
      <div className="p-3 border-t border-slate-800 space-y-2">
        <div className="flex flex-wrap gap-2">{(SCENARIOS[domain] || []).map(([label, name]) => <button key={name} className="btn" onClick={() => run(name)}>{label}</button>)}</div>
        <div className="flex gap-2">
          <input className="flex-1 bg-slate-900 border border-slate-700 rounded px-3 py-2" placeholder="type a request…" value={text}
                 onChange={(e) => setText(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} />
          <button className="btn btn-accent" onClick={send}>Send</button>
        </div>
      </div>
    </section>
  );
}
