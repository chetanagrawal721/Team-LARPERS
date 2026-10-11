// Small stroke icons (24x24). No emoji and no icon library.
const P = {
  shield: "M12 3l7 3v5c0 4.5-3 8.2-7 10-4-1.8-7-5.5-7-10V6l7-3z M9 12l2 2 4-4",
  live: "M4 12h4l2-6 4 12 2-6h4",
  lab: "M9 3h6 M10 3v6l-5 9a2 2 0 001.8 3h10.4A2 2 0 0019 18l-5-9V3",
  audit: "M7 3h8l4 4v14H7z M15 3v4h4 M10 12h6 M10 16h6",
  policy: "M12 3l8 3v6c0 4-3.2 7.5-8 9-4.8-1.5-8-5-8-9V6l8-3z",
  agents: "M12 12a4 4 0 100-8 4 4 0 000 8z M4 21c0-4 3.6-7 8-7s8 3 8 7",
  bell: "M6 9a6 6 0 1112 0c0 6 2 7 2 7H4s2-1 2-7z M10 20a2 2 0 004 0",
  chevron: "M6 9l6 6 6-6",
  check: "M5 12.5l4.5 4.5L19 7.5",
  x: "M6 6l12 12 M18 6L6 18",
  chat: "M4 5h16v11H9l-5 4z",
  warn: "M12 4l9 16H3z M12 10v4 M12 17h.01",
  info: "M12 21a9 9 0 100-18 9 9 0 000 18z M12 11v5 M12 8h.01",
  search: "M11 18a7 7 0 100-14 7 7 0 000 14z M20 20l-4-4",
  refresh: "M4 12a8 8 0 0113.7-5.6L20 8 M20 4v4h-4 M20 12a8 8 0 01-13.7 5.6L4 16 M4 20v-4h4",
  dot: "M12 12h.01",
};

export default function Icon({ name, size = 18, className = "", stroke = 1.8 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={stroke}
         strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      <path d={P[name] || P.dot} />
    </svg>
  );
}
