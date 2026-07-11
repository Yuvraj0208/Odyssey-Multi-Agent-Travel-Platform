"use client";

import { useEffect, useRef } from "react";
import { AnimatePresence } from "framer-motion";
import { useStore } from "@/lib/store";
import { MessageBubble } from "./MessageBubble";
import { Composer } from "./Composer";
import { EmptyState } from "./EmptyState";
import { AlertTriangle } from "lucide-react";

export function ChatPanel({ ready }: { ready: boolean }) {
  const messages = useStore((s) => s.messages);
  const streaming = useStore((s) => s.streaming);
  const errorBanner = useStore((s) => s.errorBanner);
  const activeAgent = useStore((s) => s.activeAgent);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [messages, streaming]);

  const empty = messages.length === 0;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto">
        {empty ? (
          <EmptyState ready={ready} />
        ) : (
          <div className="mx-auto flex max-w-2xl flex-col gap-5 px-5 py-6">
            <AnimatePresence initial={false}>
              {messages.map((m) => (
                <MessageBubble key={m.id} message={m} />
              ))}
            </AnimatePresence>
            {streaming && activeAgent && !messages.some((m) => m.streaming) && (
              <ThinkingRow agent={activeAgent} />
            )}
          </div>
        )}
      </div>

      {errorBanner && (
        <div className="mx-5 mb-2 flex items-center gap-2 rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-xs text-danger">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {errorBanner}
        </div>
      )}

      <Composer />
    </div>
  );
}

function ThinkingRow({ agent }: { agent: string }) {
  return (
    <div className="flex items-center gap-2 pl-1 text-xs text-muted">
      <span className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-1.5 w-1.5 animate-bounce rounded-full bg-accent"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </span>
      <span className="capitalize">{agent.replace(/_/g, " ")} is working...</span>
    </div>
  );
}
