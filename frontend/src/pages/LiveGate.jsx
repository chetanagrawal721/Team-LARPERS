import StatTiles from "../components/StatTiles";
import ActionStream from "../components/ActionStream";
import ActionDetail from "../components/ActionDetail";
import Icon from "../components/Icon";

export default function LiveGate({ decisions, selectedId, onSelect, onAsk, ...rest }) {
  const sel = decisions.find((d) => d.id === selectedId) || decisions[0];
  return (
    <div className="p-6 space-y-5 h-full overflow-auto">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-[22px] font-semibold">Live Gate</h1>
          <p className="text-[13px] text-[#64748b]">Monitor and decide on agent actions before they run.</p>
        </div>
        <button className="btn btn-primary" onClick={onAsk}><Icon name="chat" size={16} />Ask an agent</button>
      </div>
      <StatTiles decisions={decisions} />
      <div className="grid grid-cols-1 xl:grid-cols-[minmax(340px,5fr)_7fr] gap-5 items-start">
        <div className="xl:max-h-[calc(100vh-290px)] flex flex-col min-h-[320px]"><ActionStream decisions={decisions} selectedId={sel?.id} onSelect={onSelect} /></div>
        {sel ? <ActionDetail d={sel} {...rest} /> : <div className="card p-10 text-center text-[#64748b]">Select an action to see what it would really do.</div>}
      </div>
    </div>
  );
}
