import { tidy } from "../api";
import Icon from "./Icon";

const TONE = { HOLD: ["#b45309", "Needs approval"], BLOCK: ["#b91c1c", "Blocked"], error: ["#b91c1c", "Not allowed"], ok: ["#15803d", "Done"] };

// Compact notifications at the bottom right so they never cover the action stream.
export default function Toasts({ items, onDismiss, onReview }) {
  return (
    <div className="fixed bottom-4 right-4 z-[60] space-y-2 w-[360px]" role="status" aria-live="polite">
      {items.map((t) => {
        const [color, title] = TONE[t.level] || ["#475569", t.level];
        return (
          <div key={t.key} className="card toast-in px-4 py-3 shadow-lg" style={{ borderLeft: `3px solid ${color}` }}>
            <div className="flex justify-between items-start gap-3">
              <div className="min-w-0">
                <div className="text-[12px] font-semibold" style={{ color }}>{title}</div>
                <div className="text-[13px] text-[#334155] break-words">{tidy(t.text)}</div>
              </div>
              <button className="text-[#64748b] hover:text-[#0f172a]" onClick={() => onDismiss(t.key)} aria-label="Dismiss"><Icon name="x" size={14} /></button>
            </div>
            {t.decisionId && <button className="btn mt-2 !py-1" onClick={() => onReview(t.decisionId)}>Show</button>}
          </div>
        );
      })}
    </div>
  );
}
