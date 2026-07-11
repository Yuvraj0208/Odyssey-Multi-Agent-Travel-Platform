"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CloudRain, Info, Sparkles, X } from "lucide-react";
import { useStore } from "@/lib/store";
import { markNotificationRead } from "@/lib/api";
import { useChatStream } from "@/hooks/useChatStream";
import { cn } from "@/lib/utils";
import type { Notification } from "@/lib/types";

const TOAST_MS = 14000;

export function Toaster() {
  const notifications = useStore((s) => s.notifications);
  const markRead = useStore((s) => s.markNotificationRead);
  const { send } = useChatStream();
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  // newest unread, not-yet-dismissed, cap 3
  const visible = notifications.filter((n) => !n.read && !dismissed.has(n.id)).slice(0, 3);

  useEffect(() => {
    if (visible.length === 0) return;
    const timers = visible.map((n) =>
      setTimeout(() => setDismissed((d) => new Set(d).add(n.id)), TOAST_MS),
    );
    return () => timers.forEach(clearTimeout);
  }, [visible.map((n) => n.id).join(",")]); // eslint-disable-line react-hooks/exhaustive-deps

  function close(n: Notification) {
    setDismissed((d) => new Set(d).add(n.id));
  }
  function replan(n: Notification) {
    markRead(n.id);
    markNotificationRead(n.id);
    close(n);
    if (n.suggested_prompt) send(n.suggested_prompt);
  }

  return (
    <div className="pointer-events-none fixed bottom-5 left-1/2 z-50 flex w-[380px] max-w-[92vw] -translate-x-1/2 flex-col gap-2 xl:left-auto xl:right-5 xl:translate-x-0">
      <AnimatePresence initial={false}>
        {visible.map((n) => (
          <motion.div
            key={n.id}
            layout
            initial={{ opacity: 0, y: 20, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.97 }}
            transition={{ type: "spring", stiffness: 380, damping: 30 }}
            className="pointer-events-auto overflow-hidden rounded-2xl border border-border bg-elevated shadow-lift"
          >
            <div className="flex items-start gap-3 p-3.5">
              <span
                className={cn(
                  "mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-lg",
                  n.severity === "warning" ? "bg-amber-500/15 text-amber-400" : "bg-accent-soft text-accent",
                )}
              >
                {n.kind === "weather" ? <CloudRain className="h-4 w-4" /> : <Info className="h-4 w-4" />}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <div className="text-[13px] font-semibold text-fg">{n.title}</div>
                  <button onClick={() => close(n)} className="text-faint transition hover:text-fg">
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
                <p className="mt-0.5 text-[12px] leading-snug text-muted">{n.body}</p>
                {n.suggested_prompt && (
                  <button
                    onClick={() => replan(n)}
                    className="mt-2 inline-flex items-center gap-1.5 rounded-lg bg-accent px-2.5 py-1.5 text-[11.5px] font-medium text-accent-fg transition hover:opacity-90"
                  >
                    <Sparkles className="h-3.5 w-3.5" /> Ask agents to fix it
                  </button>
                )}
              </div>
            </div>
            <motion.div
              className="h-0.5 bg-accent/60"
              initial={{ width: "100%" }}
              animate={{ width: "0%" }}
              transition={{ duration: TOAST_MS / 1000, ease: "linear" }}
            />
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
