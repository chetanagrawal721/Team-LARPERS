import { useCallback, useEffect, useRef, useState } from "react";
import { call } from "./api";
import { useEvents } from "./hooks/useEvents";
import Sidebar from "./components/Sidebar";
import TopBar, { OrgMenu } from "./components/TopBar";
import Toasts from "./components/Toast";
import ChatDrawer from "./components/ChatDrawer";
import AccessModal from "./components/AccessModal";
import SandboxPopup from "./components/SandboxPopup";
import ApprovalSheet from "./components/ApprovalSheet";
import DiffOverlay from "./components/DiffOverlay";
import ShadowOverlay from "./components/ShadowOverlay";
import LiveGate from "./pages/LiveGate";
import AttackLab from "./pages/AttackLab";
import AuditPage from "./pages/AuditPage";
import PolicyPage from "./pages/PolicyPage";
import AgentsPage from "./pages/AgentsPage";
import AgentActivity from "./pages/AgentActivity";

export default function App() {
  const [page, setPage] = useState("gate");
  const [domain, setDomain] = useState("bank");
  const [orgs, setOrgs] = useState([]);
  const [ai, setAi] = useState(true);
  const [decisions, setDecisions] = useState([]);
  const [messages, setMessages] = useState([]);
  const [selected, setSelected] = useState(null);
  const [toasts, setToasts] = useState([]);
  const [overlay, setOverlay] = useState(null);
  const [drawer, setDrawer] = useState(false);
  const [orgMenu, setOrgMenu] = useState(false);
  const [offline, setOffline] = useState(false);
  const [working, setWorking] = useState(false);
  const [activity, setActivity] = useState([]);   // live feed: agent steps, gateway pipeline lines, sandbox rows
  const [agentMode, setAgentMode] = useState(null);
  const [access, setAccess] = useState([]);       // agents asking a person for access (newest last)
  const [draft, setDraft] = useState("");
  const [sandboxQueue, setSandboxQueue] = useState([]);   // sandbox runs waiting to be shown as an animation
  const [replay, setReplay] = useState(null);
  const [hiddenAccess, setHiddenAccess] = useState([]);
  const [tick, setTick] = useState(0);            // bumps whenever the log changes, so open pages reload
  const seen = useRef(new Set());
  const pendingUser = useRef([]);                  // typed messages already on screen, so the agent's echo is not shown twice
  const workTimer = useRef(null);
  const lockSel = useRef(0);                       // keep a voided decision on screen so its broken seal is visible

  const refresh = useCallback(async () => {
    try { setDecisions(await call("/actions?limit=100")); setOffline(false); setTick((t) => t + 1); } catch { setOffline(true); }
  }, []);
  const loadMeta = useCallback(async () => {
    try {
      setOrgs(await call("/orgs")); const d = await call("/domain"); setDomain(d.domain);
      setAi((await call("/ai/status")).enabled);
      setAgentMode(await call("/agent/mode"));
    } catch { setOffline(true); }
  }, []);
  useEffect(() => { loadMeta(); refresh(); }, [loadMeta, refresh]);

  const notify = useCallback((level, text, extra = {}) => {
    const key = Math.random().toString(36).slice(2);
    setToasts((t) => [...t.slice(-3), { key, level, text, ...extra }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.key !== key)), level === "error" ? 9000 : 5500);
  }, []);

  const onEvent = useCallback(async (e) => {
    if (e.id && seen.current.has(e.id)) return;
    seen.current.add(e.id);
    if (e.type === "chat") {
      const i = e.data.from === "user" ? pendingUser.current.indexOf(e.data.text) : -1;
      if (i >= 0) { pendingUser.current.splice(i, 1); return; }
      setMessages((m) => [...m, { ...e.data, t: e.ts }]);
      if (e.data.from !== "user") { setWorking(false); clearTimeout(workTimer.current); }
    }
    if (e.type === "access") {
      setActivity((a) => [...a.slice(-900), e]);
      if (e.data.status !== "pending") setMessages((m) => [...m, { from: "note", text: `${e.data.agent_name || e.data.agent} was ${e.data.status} access${e.data.by ? ` by ${e.data.by}` : ""}.`, t: e.ts }]);
      setAccess((list) => (list.some((a) => a.id === e.data.id) ? list.map((a) => (a.id === e.data.id ? e.data : a)) : [...list, e.data]));
      if (e.data.status === "pending") {
        setWorking(false);
      }
      return;
    }
    if (["agent", "pipeline", "sandbox"].includes(e.type)) {
      setActivity((a) => [...a.slice(-900), e]);
      if (e.type === "sandbox") setSandboxQueue((q) => [...q, e]);
      return;
    }
    if (e.type === "domain") { loadMeta(); refresh(); }
    if (["decision", "approval", "execution", "void", "shadow", "freeze"].includes(e.type)) {
      await refresh();
      if (e.type === "decision") {
        if (Date.now() > lockSel.current) setSelected(e.decision_id);
        if (["HOLD", "BLOCK"].includes(e.data.verdict)) notify(e.data.verdict, `${e.data.agent} / ${e.data.action}: ${e.data.reason}`, { decisionId: e.decision_id });
      }
      if (e.type === "void") { lockSel.current = Date.now() + 10000; setSelected(e.decision_id); }
    }
  }, [notify, refresh, loadMeta]);
  const online = useEvents(onEvent);

  const startWork = () => { setWorking(true); clearTimeout(workTimer.current); workTimer.current = setTimeout(() => setWorking(false), 60000); };
  const sendRequest = async (text, attachment = "") => {
    pendingUser.current.push(text);
    setMessages((m) => [...m, { from: "user", text, attachment, t: Date.now() / 1000 }]);
    startWork();
    try { await call("/demo/chat", { method: "POST", body: { text, attachment } }); }
    catch (e) { setWorking(false); setMessages((m) => [...m, { from: "gate", text: `The request could not be sent: ${e.message}. Check that the gateway is running.` }]); }
  };
  const decideAccess = async (id, verdict) => {
    try { await call(`/agent/access/${id}/${verdict}`, { method: "POST", auth: true }); startWork(); }
    catch (e) { notify("error", `Could not ${verdict === "grant" ? "grant" : "deny"} access: ${e.message}`); }
  };
  const openChat = () => setDrawer(true);
  const watch = () => { setDrawer(false); setPage("activity"); };
  const switchDomain = async (d) => {
    try { await call(`/domain/${d}`, { method: "POST" }); setMessages([]); setSelected(null); await loadMeta(); await refresh(); }
    catch { notify("error", "Could not switch organisation."); }
  };
  const toggleAi = async () => {
    const r = await call("/ai/toggle", { method: "POST" }); setAi(r.enabled);
    notify("ok", r.enabled ? "AI checks are on. They can only make a decision stricter." : "AI checks are off. Decisions use the rules alone, with the same safety.");
  };

  const waitingAccess = access.filter((a) => a.status === "pending");
  const pendingAccess = waitingAccess.find((a) => !hiddenAccess.includes(a.id));
  const waitingList = decisions.filter((d) => d.verdict === "HOLD" && d.status === "pending");
  const org = orgs.find((o) => o.domain === domain)?.org;
  const goDecision = (id) => { setSelected(id); setPage("gate"); };
  const common = { onChanged: refresh, notify };

  return (
    <div className="h-full flex">
      <Sidebar page={page} onPage={setPage} org={org} onOrg={() => setOrgMenu(true)} waiting={waitingList.length} />
      <div className="flex-1 min-w-0 flex flex-col">
        <TopBar pendingAccess={waitingAccess.length} onOpenAccess={() => setHiddenAccess([])} orgs={orgs} domain={domain} onDomain={switchDomain} ai={ai} onAi={toggleAi} online={online} waiting={waitingList.length}
                waitingList={waitingList} onOpenWaiting={(d) => { goDecision(d.id); setOverlay({ kind: "sheet", id: d.id }); }} menuOpen={orgMenu} setMenuOpen={setOrgMenu} />
        {(offline || !online) && <div className="bg-[#fef2f2] border-b border-[#fecaca] text-[#b91c1c] text-center py-1.5 text-[13px]" role="alert">Cannot reach the gateway. Start it with ./run.sh and this page will reconnect on its own.</div>}
        <main className="flex-1 min-h-0">
          {page === "gate" && <LiveGate decisions={decisions} selectedId={selected} onSelect={setSelected} onAsk={openChat}
                                        onSheet={(id) => setOverlay({ kind: "sheet", id })} onDiff={(d) => setOverlay({ kind: "diff", d })}
                                        onShadow={(sid) => setOverlay({ kind: "shadow", sid })} {...common} />}
          {page === "lab" && <AttackLab activity={activity} notify={notify} onReplay={setReplay} />}
          {page === "activity" && <AgentActivity activity={activity} onReplay={setReplay} />}
          {page === "audit" && <AuditPage refreshKey={tick} />}
          {page === "policy" && <PolicyPage domain={domain} onSwitchOrg={() => setOrgMenu(true)} />}
          {page === "agents" && <AgentsPage refreshKey={tick} notify={notify} access={access} />}
        </main>
      </div>
      <Toasts items={toasts} onDismiss={(k) => setToasts((t) => t.filter((x) => x.key !== k))} onReview={(id) => { goDecision(id); }} onOpenChat={openChat} />
      {drawer && <ChatDrawer domain={domain} messages={messages} working={working} onSend={sendRequest} onClose={() => setDrawer(false)}
                                mode={agentMode} draft={draft} setDraft={setDraft} onWatch={watch} />}
      {pendingAccess && <AccessModal a={pendingAccess} queued={waitingAccess.length - 1} onGrant={(id) => decideAccess(id, "grant")} onDeny={(id) => decideAccess(id, "deny")}
                                     onLater={() => setHiddenAccess((h) => [...h, pendingAccess.id])} />}
      {(replay || sandboxQueue[0]) && <SandboxPopup key={(replay || sandboxQueue[0]).id} ev={replay || sandboxQueue[0]} replay={!!replay}
                                                     onClose={() => (replay ? setReplay(null) : setSandboxQueue((q) => q.slice(1)))} />}
      {overlay?.kind === "sheet" && <ApprovalSheet id={overlay.id} onClose={() => setOverlay(null)} onChanged={refresh} notify={notify} onDiff={(d) => setOverlay({ kind: "diff", d })} />}
      {overlay?.kind === "diff" && <DiffOverlay d={overlay.d} onClose={() => setOverlay(null)} />}
      {overlay?.kind === "shadow" && <ShadowOverlay sid={overlay.sid} onClose={() => setOverlay(null)} notify={notify} onChanged={refresh} />}
    </div>
  );
}
