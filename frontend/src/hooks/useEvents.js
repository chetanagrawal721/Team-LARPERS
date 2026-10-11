import { useEffect, useRef, useState } from "react";
import { API } from "../api";

// Live event stream with automatic reconnect (EventSource reconnects on its own; we also surface connection state).
export function useEvents(onEvent) {
  const [online, setOnline] = useState(false);
  const handler = useRef(onEvent);
  handler.current = onEvent;

  useEffect(() => {
    let es; let stop = false; let timer;
    const types = ["decision", "approval", "execution", "void", "chat", "shadow", "audit", "freeze", "domain", "ai"];
    const open = () => {
      es = new EventSource(`${API}/events`);
      es.onopen = () => setOnline(true);
      es.onerror = () => {
        setOnline(false);
        es.close();
        if (!stop) timer = setTimeout(open, 1500);
      };
      types.forEach((t) => es.addEventListener(t, (e) => {
        try { handler.current({ id: Number(e.lastEventId), ...JSON.parse(e.data) }); } catch { /* ignore bad frame */ }
      }));
    };
    open();
    return () => { stop = true; clearTimeout(timer); es && es.close(); };
  }, []);

  return online;
}
