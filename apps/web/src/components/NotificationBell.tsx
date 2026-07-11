"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Bell, CloudRain, Info, Sparkles } from "lucide-react";
import { useStore } from "@/lib/store";
import { markNotificationRead } from "@/lib/api";
import { useChatStream } from "@/hooks/useChatStream";
import { cn } from "@/lib/utils";

export function NotificationBell() {
  const notifications = useStore((s) => s.notifications);
  const markRead = useStore((s) => s.markNotificationRead);
  const { send } = useChatStream();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const unread = notifications.filter((n) => !n.read).length;

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        aria-label="Notifications"
        className="relative grid h-9 w-9 place-items-center rounded-lg border border-border text-muted transition hover:bg-surface-2 hover:text-fg"
      >
        <Bell className="h-4 w-4" />
        {unread > 0 && (
          <span className="absolute -right-1 -top-1 grid h-4 min-w-4 place-items-center rounded-full bg-accent px-1 text-[10px] font-bold text-accent-fg">
            {unread}
          </span>
        )}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.98 }}
            transition={{ duration: 0.16 }}
            className="absolute right-0 z-50 mt-2 w-[340px] overflow-hidden rounded-2xl border border-border bg-elevated shadow-lift"
          >
            <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
              <div className="text-[13px] font-semibold">Notifications</div>
              <span className="text-[11px] text-faint">{notifications.length} total</span>
            </div>
            <div className="max-h-[360px] overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="px-4 py-8 text-center text-xs text-faint">
                  No notifications yet. Odyssey will nudge you if conditions change.
                </div>
              ) : (
                notifications.map((n) => (
                  <div
                    key={n.id}
                    className={cn(
                      "flex items-start gap-2.5 border-b border-border px-3.5 py-3 last:border-0",
                      !n.read && "bg-accent-soft/40",
                    )}
                  >
                    <span
                      className={cn(
                        "mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg",
                        n.severity === "warning" ? "bg-amber-500/15 text-amber-400" : "bg-accent-soft text-accent",
                      )}
                    >
                      {n.kind === "weather" ? <CloudRain className="h-3.5 w-3.5" /> : <Info className="h-3.5 w-3.5" />}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="text-[12.5px] font-medium text-fg">{n.title}</div>
                      <p className="mt-0.5 text-[11.5px] leading-snug text-muted">{n.body}</p>
                      {n.suggested_prompt && (
                        <button
                          onClick={() => {
                            markRead(n.id);
                            markNotificationRead(n.id);
                            setOpen(false);
                            send(n.suggested_prompt!);
                          }}
                          className="mt-1.5 inline-flex items-center gap-1 text-[11px] font-medium text-accent transition hover:underline"
                        >
                          <Sparkles className="h-3 w-3" /> Ask agents to fix it
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
