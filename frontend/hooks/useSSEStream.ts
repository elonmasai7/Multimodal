"use client";

import { useCallback, useRef, useState } from "react";

import { useLearningStore } from "@/store/learningStore";
import type { StreamEventType, StreamItem, StreamPayload } from "@/types/stream";

const eventTypes: StreamEventType[] = [
  "status",
  "error",
  "narration",
  "text",
  "image",
  "audio",
  "video",
  "quiz",
  "simulation",
  "done"
];

export function useSSEStream() {
  const pushEvent = useLearningStore((s) => s.pushEvent);
  const clearStream = useLearningStore((s) => s.clearStream);
  const sourceRef = useRef<EventSource | null>(null);
  const [connected, setConnected] = useState(false);

  const disconnect = useCallback(() => {
    sourceRef.current?.close();
    sourceRef.current = null;
    setConnected(false);
  }, []);

  const connect = useCallback(
    (url: string) => {
      disconnect();
      clearStream();

      const source = new EventSource(url);
      sourceRef.current = source;

      eventTypes.forEach((type) => {
        source.addEventListener(type, (event) => {
          let payload: StreamPayload = {};
          try {
            payload = JSON.parse((event as MessageEvent).data) as StreamPayload;
          } catch {
            payload = { data: { raw: (event as MessageEvent).data } };
          }

          const item: StreamItem = {
            id: crypto.randomUUID(),
            type,
            payload
          };

          pushEvent(item);
          if (type === "done") {
            setConnected(false);
            source.close();
          }
        });
      });

      source.onopen = () => setConnected(true);
      source.onerror = () => {
        setConnected(false);
        source.close();
      };
    },
    [clearStream, disconnect, pushEvent]
  );

  return { connect, disconnect, connected };
}
