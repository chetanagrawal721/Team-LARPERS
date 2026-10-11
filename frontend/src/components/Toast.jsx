// Top-right popups for HOLD / BLOCK decisions (and operation results).
export default function Toasts({ items, onDismiss, onReview, onSafe }) {
  return (
    <div className="fixed top-16 right-4 z-40 space-y-2 w-96">
      {items.map((t) => (
        <div key={t.key} className={`rounded-lg border p-3 shadow-xl bg-slate-900 toast-in ${t.level === "HOLD" ? "border-amber-500/60" : t.level === "BLOCK" ? "border-rose-500/60" : t.level === "error" ? "border-rose-500/60" : "border-slate-600"}`}>
          <div className="flex justify-between text-sm">
            <b>{t.level === "HOLD" ? "🟡 Approval needed" : t.level === "BLOCK" ? "🔴 Blocked" : t.level === "error" ? "⚠ Refused" : "✓"}</b>
            <button onClick={() => onDismiss(t.key)} aria-label="dismiss">✕</button>
          </div>
          <div className="text-sm mt-1">{t.text}</div>
          {t.decisionId && (
            <div className="flex gap-2 mt-2">
              <button className="btn" onClick={() => onReview(t.decisionId)}>Review</button>
              {t.safe && <button className="btn btn-accent" onClick={() => onSafe(t.decisionId)}>Approve safe version</button>}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
