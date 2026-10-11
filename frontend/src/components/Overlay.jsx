import { useEffect } from "react";

// Modal shell: closes with Esc and on click outside.
export default function Overlay({ title, onClose, children, wide = false }) {
  useEffect(() => {
    const h = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);
  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-6" onClick={onClose}>
      <div className={`bg-[#ffffff] border border-[#d0d7de] rounded-lg max-h-[88vh] overflow-auto ${wide ? "w-[1100px]" : "w-[820px]"} max-w-full`} onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 py-3 border-b border-[#d0d7de] sticky top-0 bg-[#ffffff]">
          <h2 className="font-semibold">{title}</h2>
          <button onClick={onClose} aria-label="close" className="text-[#59636e] hover:text-[#1f2328]">Close (Esc)</button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}
