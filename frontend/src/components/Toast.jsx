import { tidy } from "../api";

const TONE = { HOLD: "#d29922", BLOCK: "#f85149", error: "#f85149", ok: "#3fb950" };
const TITLE = { HOLD: "Needs approval", BLOCK: "Blocked", error: "Not allowed", ok: "Done" };

// Compact notifications, bottom right so they never cover the live list.
export default function Toasts({ items, onDismiss, onReview }) {
  return (
    <div className="fixed bottom-4 right-4 z-40 space-y-2 w-[360px]" role="status" aria-live="polite">
      {items.map((t) => (
        <div key={t.key} className="panel toast-in px-3 py-2.5 shadow-lg" style={{ borderLeft: `3px solid ${TONE[t.level] || "#8b949e"}` }}>
          <div className="flex justify-between items-start gap-3">
            <div className="min-w-0">
              <div className="text-[12px] font-semibold" style={{ color: TONE[t.level] }}>{TITLE[t.level] || t.level}</div>
              <div className="text-[13px] text-[#c9d1d9] break-words">{tidy(t.text)}</div>
            </div>
            <button className="text-[#8b949e] hover:text-white text-[13px]" onClick={() => onDismiss(t.key)} aria-label="Dismiss">Close</button>
          </div>
          {t.decisionId && <button className="btn mt-2" onClick={() => onReview(t.decisionId)}>Show</button>}
        </div>
      ))}
    </div>
  );
}
