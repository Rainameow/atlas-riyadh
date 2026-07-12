// Subscribes to the backend's per-tick WebSocket stream and exposes the latest
// tick plus a connection status. Reconnects automatically with backoff.

import { useEffect, useRef, useState } from "react";
import type { TickMessage } from "../types";

type Status = "connecting" | "open" | "closed";

export function useSimulationSocket() {
  const [tick, setTick] = useState<TickMessage | null>(null);
  const [status, setStatus] = useState<Status>("connecting");
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let closed = false;
    let retry = 500;
    let timer: ReturnType<typeof setTimeout>;

    const connect = () => {
      const proto = window.location.protocol === "https:" ? "wss" : "ws";
      const ws = new WebSocket(`${proto}://${window.location.host}/ws/stream`);
      socketRef.current = ws;
      setStatus("connecting");

      ws.onopen = () => {
        retry = 500;
        setStatus("open");
      };
      ws.onmessage = (event) => {
        try {
          setTick(JSON.parse(event.data) as TickMessage);
        } catch {
          /* ignore malformed frames */
        }
      };
      ws.onclose = () => {
        setStatus("closed");
        if (!closed) {
          timer = setTimeout(connect, retry);
          retry = Math.min(retry * 2, 5000);
        }
      };
      ws.onerror = () => ws.close();
    };

    connect();
    return () => {
      closed = true;
      clearTimeout(timer);
      socketRef.current?.close();
    };
  }, []);

  return { tick, status };
}
