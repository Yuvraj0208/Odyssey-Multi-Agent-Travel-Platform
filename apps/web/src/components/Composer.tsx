"use client";

import { useState, useRef, useEffect } from "react";
import { ArrowUp, Square } from "lucide-react";
import { useChatStream } from "@/hooks/useChatStream";
import { useStore } from "@/lib/store";
import { cn } from "@/lib/utils";

export function Composer() {
  const [text, setText] = useState("");
  const streaming = useStore((s) => s.streaming);
  const sessionId = useStore((s) => s.sessionId);
  const { send, stop } = useChatStream();
  const taRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
  }, [text]);

  async function submit() {
    if (streaming) return;
    const t = text;
    setText("");
    await send(t);
  }

  return (
    <div className="border-t border-border bg-surface/70 p-3 backdrop-blur">
      <div
        className={cn(
          "mx-auto flex max-w-2xl items-end gap-2 rounded-2xl border border-border bg-surface px-3 py-2 shadow-soft transition focus-within:border-accent/50 focus-within:shadow-glow",
        )}
      >
        <textarea
          ref={taRef}
          rows={1}
          value={text}
          disabled={!sessionId}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder="Describe your trip - where, when, who, and what you love..."
          className="max-h-40 flex-1 resize-none bg-transparent py-1.5 text-[14px] leading-relaxed text-fg outline-none placeholder:text-faint"
        />
        {streaming ? (
          <button
            onClick={stop}
            className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-surface-2 text-fg transition hover:bg-elevated"
            aria-label="Stop"
          >
            <Square className="h-4 w-4" />
          </button>
        ) : (
          <button
            onClick={submit}
            disabled={!text.trim()}
            className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-accent text-accent-fg transition enabled:hover:opacity-90 disabled:opacity-40"
            aria-label="Send"
          >
            <ArrowUp className="h-4 w-4" />
          </button>
        )}
      </div>
      <p className="mx-auto mt-1.5 max-w-2xl px-1 text-center text-[10.5px] text-faint">
        Odyssey plans with real open data. Bookings always ask before confirming.
      </p>
    </div>
  );
}
