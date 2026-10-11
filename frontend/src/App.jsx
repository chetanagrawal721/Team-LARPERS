import { useCallback, useEffect, useRef, useState } from "react";
import { call } from "./api";
import { useEvents } from "./hooks/useEvents";
import Sidebar from "./components/Sidebar";
import TopBar, { OrgMenu } from "./components/TopBar";
import Toasts from "./components/Toast";
import ChatDrawer from "./components/ChatDrawer";
import ApprovalSheet from "./components/ApprovalSheet";
import DiffOverlay from "./components/DiffOverlay";
import ShadowOverlay from "./components/ShadowOverlay";
import LiveGate from "./pages/LiveGate";
import AttackLab from "./pages/AttackLab";
import AuditPage from "./pages/AuditPage";
import PolicyPage from "./pages/PolicyPage";
import AgentsPage from "./pages/AgentsPage";

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
  const [tab, setTab] = useState("chat");
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
      setMessages((m) => [...m, e.data]);
      if (e.data.from !== "user") { setWorking(false); clearTimeout(workTimer.current); }
    }
    if (["agent", "pipeline", "sandbox"].includes(e.type)) { setActivity((a) => [...a.slice(-700), e]); return; }
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
  const sendRequest = async (text) => {
    pendingUser.current.push(text);
    setMessages((m) => [...m, { from: "user", text }]);
    if (tab !== "chat" && tab !== "prompts" && tab !== "agents") setTab("activity");
    startWork();
    try { await call("/demo/chat", { method: "POST", body: { text } }); }
    catch (e) { setWorking(false); setMessages((m) => [...m, { from: "gate", text: `The request could not be sent: ${e.message}. Check that the gateway is running.` }]); }
  };
  const runScenario = async (name) => {
    startWork();
    try { await call(`/demo/${name}`, { method: "POST" }); }
    catch (e) { setWorking(false); setMessages((m) => [...m, { from: "gate", text: `The scenario could not be started: ${e.message}.` }]); }
  };
  const changeMode = async (m) => { try { setAgentMode(await call("/agent/mode", { method: "POST", body: { mode: m } })); } catch (e) { notify("error", e.message); } };
  const switchDomain = async (d) => {
    try { await call(`/domain/${d}`, { method: "POST" }); setMessages([]); setSelected(null); await loadMeta(); await refresh(); }
    catch { notify("error", "Could not switch organisation."); }
  };
  const toggleAi = async () => {
    const r = await call("/ai/toggle", { method: "POST" }); setAi(r.enabled);
    notify("ok", r.enabled ? "AI checks are on. They can only make a decision stricter." : "AI checks are off. Decisions use the rules alone, with the same safety.");
  };

  const waitingList = decisions.filter((d) => d.verdict === "HOLD" && d.status === "pending");
  const org = orgs.find((o) => o.domain === domain)?.org;
  const goDecision = (id) => { setSelected(id); setPage("gate"); };
  const common = { onChanged: refresh, notify };

  return (
    <div className="h-full flex">
      <Sidebar page={page} onPage={setPage} org={org} onOrg={() => setOrgMenu(true)} waiting={waitingList.length} />
      <div className="flex-1 min-w-0 flex flex-col">
        <TopBar orgs={orgs} domain={domain} onDomain={switchDomain} ai={ai} onAi={toggleAi} online={online} waiting={waitingList.length}
                waitingList={waitingList} onOpenWaiting={(d) => { goDecision(d.id); setOverlay({ kind: "sheet", id: d.id }); }} menuOpen={orgMenu} setMenuOpen={setOrgMenu} />
        {(offline || !online) && <div className="bg-[#fef2f2] border-b border-[#fecaca] text-[#b91c1c] text-center py-1.5 text-[13px]" role="alert">Cannot reach the gateway. Start it with ./run.sh and this page will reconnect on its own.</div>}
        <main className="flex-1 min-h-0">
          {page === "gate" && <LiveGate decisions={decisions} selectedId={selected} onSelect={setSelected} onAsk={() => setDrawer(true)}
                                        onSheet={(id) => setOverlay({ kind: "sheet", id })} onDiff={(d) => setOverlay({ kind: "diff", d })}
                                        onShadow={(sid) => setOverlay({ kind: "shadow", sid })} {...common} />}
          {page === "lab" && <AttackLab />}
          {page === "audit" && <AuditPage refreshKey={tick} />}
          {page === "policy" && <PolicyPage domain={domain} onSwitchOrg={() => setOrgMenu(true)} />}
          {page === "agents" && <AgentsPage refreshKey={tick} notify={notify} />}
        </main>
      </div>
      <Toasts items={toasts} onDismiss={(k) => setToasts((t) => t.filter((x) => x.key !== k))} onReview={(id) => { goDecision(id); }} />
      {drawer && <ChatDrawer domain={domain} messages={messages} working={working} onSend={sendRequest} onRun={runScenario} onClose={() => setDrawer(false)}
                                activity={activity} mode={agentMode} onMode={changeMode} tab={tab} setTab={setTab} />}
      {overlay?.kind === "sheet" && <ApprovalSheet id={overlay.id} onClose={() => setOverlay(null)} onChanged={refresh} notify={notify} onDiff={(d) => setOverlay({ kind: "diff", d })} />}
      {overlay?.kind === "diff" && <DiffOverlay d={overlay.d} onClose={() => setOverlay(null)} />}
      {overlay?.kind === "shadow" && <ShadowOverlay sid={overlay.sid} onClose={() => setOverlay(null)} notify={notify} onChanged={refresh} />}
    </div>
  );
}
