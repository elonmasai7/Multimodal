"use client";

import { useCallback, useRef, useState } from "react";

export function useWebSocketStream(url: string) {
  const ref = useRef<WebSocket | null>(null);
  const [messages, setMessages] = useState<string[]>([]);
  const [connected, setConnected] = useState(false);

  const connect = useCallback(() => {
    ref.current?.close();
    const ws = new WebSocket(url);
    ref.current = ws;
    ws.onopen = () => setConnected(true);
    ws.onmessage = (event) => setMessages((prev) => [event.data, ...prev].slice(0, 50));
    ws.onclose = () => setConnected(false);
  }, [url]);

  const send = useCallback((msg: string) => ref.current?.send(msg), []);
  const close = useCallback(() => ref.current?.close(), []);

  return { messages, connected, connect, send, close };
}
