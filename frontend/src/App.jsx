import { useCallback, useEffect, useRef, useState } from "react";
import { call } from "./api";
import { useEvents } from "./hooks/useEvents";
import TopBar from "./components/TopBar";
import ChatPanel from "./components/ChatPanel";
import Console from "./components/Console";
import Toasts from "./components/Toast";
import DiffOverlay from "./components/DiffOverlay";
import ShadowOverlay from "./components/ShadowOverlay";
import AuditDrawer from "./components/AuditDrawer";
import AttackLab from "./pages/AttackLab";

export default function App() {
  const [page, setPage] = useState("gate");
  const [domain, setDomain] = useState("bank");
  const [org, setOrg] = useState("");
  const [ai, setAi] = useState(true);
  const [decisions, setDecisions] = useState([]);
  const [messages, setMessages] = useState([]);
  const [selected, setSelected] = useState(null);
  const [toasts, setToasts] = useState([]);
  const [overlay, setOverlay] = useState(null);
  const [offline, setOffline] = useState(false);
  const seen = useRef(new Set());
  const [working, setWorking] = useState(false);
  const pendingUser = useRef([]);   // typed messages already shown, so the agent's echo of them is not shown twice
  const workTimer = useRef(null);
  const lockSel = useRef(0);   // keep a voided decision on screen so its broken seal is visible

  const refresh = useCallback(async () => {
    try { setDecisions(await call("/actions?limit=40")); setOffline(false); } catch { setOffline(true); }
  }, []);
  const loadMeta = useCallback(async () => {
    try {
      const d = await call("/domain"); setDomain(d.domain); setOrg(d.org);
      const a = await call("/ai/status"); setAi(a.enabled);
    } catch { setOffline(true); }
  }, []);
  useEffect(() => { loadMeta(); refresh(); }, [loadMeta, refresh]);

  const notify = useCallback((level, text, extra = {}) => {
    const key = Math.random().toString(36).slice(2);
    setToasts((t) => [...t.slice(-3), { key, level, text, ...extra }]);
    if (!extra.sticky) setTimeout(() => setToasts((t) => t.filter((x) => x.key !== key)), level === "error" ? 8000 : 5000);
  }, []);

  const onEvent = useCallback(async (e) => {
    if (e.id && seen.current.has(e.id)) return;
    seen.current.add(e.id);
    if (e.type === "chat") {
      const i = e.data.from === "user" ? pendingUser.current.indexOf(e.data.text) : -1;
      if (i >= 0) { pendingUser.current.splice(i, 1); return; }          // already on screen
      setMessages((m) => [...m, e.data]);
      if (e.data.from !== "user") { setWorking(false); clearTimeout(workTimer.current); }
    }
    if (e.type === "domain") loadMeta();
    if (["decision", "approval", "execution", "void", "shadow"].includes(e.type)) {
      await refresh();
      if (e.type === "decision" && ["HOLD", "BLOCK"].includes(e.data.verdict)) {
        if (Date.now() > lockSel.current) setSelected(e.decision_id);
        notify(e.data.verdict, `${e.data.agent} / ${e.data.action}: ${e.data.reason}`, { decisionId: e.decision_id });
      }
      if (e.type === "void") { lockSel.current = Date.now() + 10000; setSelected(e.decision_id); }
    }
  }, [notify, refresh, loadMeta]);
  const online = useEvents(onEvent);

  const sendRequest = async (text) => {
    pendingUser.current.push(text);
    setMessages((m) => [...m, { from: "user", text }]);
    setWorking(true);
    clearTimeout(workTimer.current);
    workTimer.current = setTimeout(() => setWorking(false), 60000);
    try { await call("/demo/chat", { method: "POST", body: { text } }); }
    catch (e) {
      setWorking(false);
      setMessages((m) => [...m, { from: "gate", text: `The request could not be sent: ${e.message}. Check that the gateway is running.` }]);
    }
  };
  const runScenario = async (name) => {
    setWorking(true);
    clearTimeout(workTimer.current);
    workTimer.current = setTimeout(() => setWorking(false), 60000);
    try { await call(`/demo/${name}`, { method: "POST" }); }
    catch (e) { setWorking(false); setMessages((m) => [...m, { from: "gate", text: `The scenario could not be started: ${e.message}.` }]); }
  };
  const switchDomain = async (d) => {
    try { await call(`/domain/${d}`, { method: "POST" }); setMessages([]); setSelected(null); await loadMeta(); await refresh(); }
    catch { notify("error", "Could not switch organisation."); }
  };
  const toggleAi = async () => { const r = await call("/ai/toggle", { method: "POST" }); setAi(r.enabled); notify("ok", r.enabled ? "AI checks are on. They can only make a decision stricter." : "AI checks are off. Decisions use the rules alone, with the same safety."); };

  return (
    <div className="h-full flex flex-col">
      <TopBar domain={domain} org={org} onDomain={switchDomain} ai={ai} onAi={toggleAi} page={page} onPage={setPage}
              online={online} onAudit={() => setOverlay({ kind: "audit" })} />
      {(offline || !online) && <div className="bg-[#cf222e22] border-b border-[#cf222e55] text-[#cf222e] text-center py-1.5 text-[13px]" role="alert">Cannot reach the gateway. Start it with ./run.sh and this page will reconnect on its own.</div>}
      {page === "lab" ? <div className="flex-1 min-h-0"><AttackLab /></div> : (
        <main className="flex-1 min-h-0 grid grid-cols-[minmax(300px,2fr)_3fr]">
          <ChatPanel domain={domain} messages={messages} working={working} onSend={sendRequest} onRun={runScenario} />
          <Console decisions={decisions} selectedId={selected} onSelect={setSelected}
                   onOpenDiff={(d) => setOverlay({ kind: "diff", d })} onOpenShadow={(sid) => setOverlay({ kind: "shadow", sid })}
                   onChanged={refresh} notify={notify} />
        </main>
      )}
      <Toasts items={toasts} onDismiss={(k) => setToasts((t) => t.filter((x) => x.key !== k))}
              onReview={(id) => { setSelected(id); setPage("gate"); }} />
      {overlay?.kind === "diff" && <DiffOverlay d={overlay.d} onClose={() => setOverlay(null)} />}
      {overlay?.kind === "shadow" && <ShadowOverlay sid={overlay.sid} onClose={() => { setOverlay(null); refresh(); }} notify={notify} />}
      {overlay?.kind === "audit" && <AuditDrawer onClose={() => setOverlay(null)} />}
    </div>
  );
}
