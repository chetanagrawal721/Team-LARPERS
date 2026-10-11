// Seal mark: intact (blue), cracked (red, animated) or not yet issued (grey, dashed).
export default function Seal({ state = "none", size = 40 }) {
  const color = state === "intact" ? "#58a6ff" : state === "cracked" ? "#f85149" : "#6e7681";
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" role="img" aria-label={`Seal ${state === "none" ? "not issued" : state}`}
         className={state === "cracked" ? "seal-crack" : ""}>
      <circle cx="24" cy="24" r="19" fill="none" stroke={color} strokeWidth="2.5" strokeDasharray={state === "none" ? "3 4" : "0"} />
      {state === "cracked"
        ? <path d="M25 6l-5 13 8 6-7 9 4 8" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        : <path d="M16 24.5l5.5 5.5L32 18" fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" opacity={state === "none" ? 0.4 : 1} />}
    </svg>
  );
}
