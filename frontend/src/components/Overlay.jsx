import { useEffect } from "react";
import Icon from "./Icon";

// Modal shell: closes with Esc and on click outside. Focus returns to the page when it closes.
export default function Overlay({ title, subtitle, onClose, children, footer, width = 760, badge }) {
  useEffect(() => {
    const h = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);
  return (
    <div className="fixed inset-0 z-50 bg-[#0f172a]/45 flex items-start justify-center p-6 overflow-auto" onClick={onClose} role="dialog" aria-modal="true" aria-label={title}>
      <div className="card shadow-2xl w-full my-6" style={{ maxWidth: width }} onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between gap-4 px-6 pt-5 pb-3">
          <div>
            <h2 className="text-[17px] font-semibold flex items-center gap-2">{badge}{title}</h2>
            {subtitle && <p className="text-[13px] text-[#64748b] mt-0.5">{subtitle}</p>}
          </div>
          <button onClick={onClose} aria-label="Close" className="p-1 rounded-md text-[#64748b] hover:bg-[#f1f5f9]"><Icon name="x" /></button>
        </div>
        <div className="px-6 pb-5">{children}</div>
        {footer && <div className="px-6 py-4 border-t border-[#eef1f6] bg-[#fafbfd] rounded-b-xl">{footer}</div>}
      </div>
    </div>
  );
}
