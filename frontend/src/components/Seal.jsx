// Seal icon: intact (cyan), cracked (red, animated) or not yet issued (grey).
export default function Seal({ state = "none", size = 44 }) {
  const color = state === "intact" ? "#22d3ee" : state === "cracked" ? "#fb7185" : "#64748b";
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" className={state === "cracked" ? "seal-crack" : ""} aria-label={`seal ${state}`}>
      <circle cx="24" cy="24" r="20" fill="none" stroke={color} strokeWidth="3" strokeDasharray={state === "none" ? "4 4" : "0"} />
      <path d="M16 24l6 6 11-12" fill="none" stroke={color} strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round"
            style={{ opacity: state === "cracked" ? 0 : 1 }} />
      {state === "cracked" && <path d="M24 5l-4 12 7 5-6 8 3 9" fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />}
    </svg>
  );
}
