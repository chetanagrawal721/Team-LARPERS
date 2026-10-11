import { tidy } from "../api";

const TONE = { HOLD: "#9a6700", BLOCK: "#cf222e", error: "#cf222e", ok: "#1a7f37" };
const TITLE = { HOLD: "Needs approval", BLOCK: "Blocked", error: "Not allowed", ok: "Done" };

// Compact notifications, bottom right so they never cover the live list.
export default function Toasts({ items, onDismiss, onReview }) {
  return (
    <div className="fixed bottom-4 right-4 z-40 space-y-2 w-[360px]" role="status" aria-live="polite">
      {items.map((t) => (
        <div key={t.key} className="panel toast-in px-3 py-2.5 shadow-lg" style={{ borderLeft: `3px solid ${TONE[t.level] || "#59636e"}` }}>
          <div className="flex justify-between items-start gap-3">
            <div className="min-w-0">
              <div className="text-[12px] font-semibold" style={{ color: TONE[t.level] }}>{TITLE[t.level] || t.level}</div>
              <div className="text-[13px] text-[#3d444d] break-words">{tidy(t.text)}</div>
            </div>
            <button className="text-[#59636e] hover:text-[#1f2328] text-[13px]" onClick={() => onDismiss(t.key)} aria-label="Dismiss">Close</button>
          </div>
          {t.decisionId && <button className="btn mt-2" onClick={() => onReview(t.decisionId)}>Show</button>}
        </div>
      ))}
    </div>
  );
}
