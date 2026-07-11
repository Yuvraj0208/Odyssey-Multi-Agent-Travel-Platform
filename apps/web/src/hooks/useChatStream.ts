"use client";

import { useCallback, useRef } from "react";
import { streamChat } from "@/lib/api";
import { useStore } from "@/lib/store";

/** Drives one conversational turn: optimistic user message -> SSE -> store events. */
export function useChatStream() {
  const abortRef = useRef<AbortController | null>(null);
  const { sessionId, addUserMessage, beginTurn, endTurn, applyEvent } = useStore();

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || !sessionId) return;
      addUserMessage(trimmed);
      beginTurn();
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      try {
        await streamChat(sessionId, trimmed, (ev) => applyEvent(ev), ctrl.signal);
      } catch (e: any) {
        if (e?.name !== "AbortError") {
          applyEvent({ type: "error", ts: Date.now(), data: { message: e?.message || "Connection lost." } });
        }
      } finally {
        endTurn();
        abortRef.current = null;
      }
    },
    [sessionId, addUserMessage, beginTurn, endTurn, applyEvent],
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
    endTurn();
  }, [endTurn]);

  return { send, stop };
}
