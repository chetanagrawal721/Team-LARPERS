import Icon from "./Icon";

const Tile = ({ label, value, sub, tone, icon }) => (
  <div className="card px-5 py-4 flex items-center gap-4">
    <span className={`w-10 h-10 rounded-full grid place-items-center ${tone}`}><Icon name={icon} size={18} /></span>
    <div>
      <div className="text-[12px] text-[#64748b]">{label}</div>
      <div className="text-2xl font-semibold leading-tight">{value}</div>
      {sub && <div className="text-[12px] text-[#64748b]">{sub}</div>}
    </div>
  </div>
);

export default function StatTiles({ decisions }) {
  const total = decisions.length;
  const allowed = decisions.filter((d) => d.status === "done" && d.verdict === "ALLOW" || d.status === "allowed").length;
  const hold = decisions.filter((d) => d.verdict === "HOLD" && ["pending", "approved", "shadow"].includes(d.status)).length;
  const blocked = decisions.filter((d) => d.verdict === "BLOCK" || d.status === "void").length;
  const pct = (n) => (total ? `${Math.round((100 * n) / total)}%` : "0%");
  return (
    <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
      <Tile label="Total actions" value={total} sub="in this session" tone="bg-[#e0ecff] text-[#2563eb]" icon="live" />
      <Tile label="Allowed" value={allowed} sub={pct(allowed)} tone="bg-[#dcfce7] text-[#15803d]" icon="check" />
      <Tile label="On hold" value={hold} sub={pct(hold)} tone="bg-[#fef3c7] text-[#b45309]" icon="warn" />
      <Tile label="Blocked" value={blocked} sub={pct(blocked)} tone="bg-[#fee2e2] text-[#b91c1c]" icon="x" />
    </div>
  );
}
