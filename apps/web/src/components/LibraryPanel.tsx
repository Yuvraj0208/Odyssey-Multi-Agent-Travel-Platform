"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Brain,
  Clock,
  MapPin,
  Plus,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import { addMemory, deleteMemory, getMemories, listSessions } from "@/lib/api";
import { cn } from "@/lib/utils";

export type LibraryTab = "trips" | "preferences";

function timeAgo(ts: number): string {
  const s = Math.max(0, Date.now() / 1000 - ts);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

export function LibraryPanel({
  tab,
  onClose,
  onLoadSession,
}: {
  tab: LibraryTab | null;
  onClose: () => void;
  onLoadSession: (id: string) => void;
}) {
  const [active, setActive] = useState<LibraryTab>("trips");
  useEffect(() => {
    if (tab) setActive(tab);
  }, [tab]);

  return (
    <AnimatePresence>
      {tab && (
        <>
          <motion.div
            className="fixed inset-0 z-[55] bg-black/40 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.aside
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 320, damping: 34 }}
            className="fixed right-0 top-0 z-[56] flex h-full w-[380px] max-w-[92vw] flex-col border-l border-border bg-surface"
          >
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <div className="flex gap-1 rounded-lg bg-surface-2 p-0.5">
                {(["trips", "preferences"] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => setActive(t)}
                    className={cn(
                      "rounded-md px-3 py-1.5 text-xs font-medium capitalize transition",
                      active === t ? "bg-surface text-fg shadow-soft" : "text-muted hover:text-fg",
                    )}
                  >
                    {t}
                  </button>
                ))}
              </div>
              <button onClick={onClose} className="grid h-8 w-8 place-items-center rounded-lg text-muted transition hover:bg-surface-2 hover:text-fg">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto p-4">
              {active === "trips" ? (
                <TripsTab onLoadSession={onLoadSession} onClose={onClose} />
              ) : (
                <PreferencesTab />
              )}
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

function TripsTab({ onLoadSession, onClose }: { onLoadSession: (id: string) => void; onClose: () => void }) {
  const [sessions, setSessions] = useState<any[] | null>(null);
  useEffect(() => {
    listSessions().then(setSessions);
  }, []);

  if (sessions === null) return <Skeleton rows={4} />;
  if (sessions.length === 0)
    return <Empty icon={<Clock className="h-5 w-5" />} text="No trips yet. Plan one to see it here." />;

  return (
    <div className="space-y-2">
      {sessions.map((s) => (
        <button
          key={s.session_id}
          onClick={() => {
            onLoadSession(s.session_id);
            onClose();
          }}
          className="group flex w-full items-center gap-3 rounded-xl border border-border bg-surface-2/40 px-3 py-2.5 text-left transition hover:border-accent/40 hover:bg-surface-2"
        >
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-accent-soft text-accent">
            <MapPin className="h-4 w-4" />
          </span>
          <div className="min-w-0 flex-1">
            <div className="truncate text-[13px] font-medium text-fg">{s.title || s.destination || "New trip"}</div>
            <div className="text-[11px] text-faint">{timeAgo(s.updated_at)}</div>
          </div>
          <Sparkles className="h-4 w-4 text-faint transition group-hover:text-accent" />
        </button>
      ))}
    </div>
  );
}

function PreferencesTab() {
  const [mems, setMems] = useState<any[] | null>(null);
  const [text, setText] = useState("");
  const refresh = () => getMemories().then(setMems);
  useEffect(() => {
    refresh();
  }, []);

  async function add() {
    const t = text.trim();
    if (!t) return;
    setText("");
    await addMemory(t);
    refresh();
  }
  async function remove(key: string) {
    await deleteMemory(key);
    refresh();
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-[12px] text-muted">
        <Brain className="h-4 w-4 text-accent" />
        What Odyssey remembers about how you travel. Agents use these to personalize.
      </div>
      <div className="flex gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
          placeholder="Add a preference, e.g. window seats"
          className="flex-1 rounded-lg border border-border bg-surface-2 px-3 py-2 text-[13px] text-fg outline-none placeholder:text-faint focus:border-accent/50"
        />
        <button onClick={add} className="grid h-9 w-9 place-items-center rounded-lg bg-accent text-accent-fg transition hover:opacity-90">
          <Plus className="h-4 w-4" />
        </button>
      </div>
      {mems === null ? (
        <Skeleton rows={3} />
      ) : mems.length === 0 ? (
        <Empty icon={<Brain className="h-5 w-5" />} text="No preferences yet. Add one, or plan a trip and Odyssey learns as you go." />
      ) : (
        <div className="space-y-1.5">
          {mems.map((m) => (
            <div key={m.key} className="group flex items-start gap-2 rounded-lg border border-border bg-surface-2/40 px-3 py-2">
              <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
              <div className="min-w-0 flex-1">
                <div className="text-[12.5px] text-fg">{m.text}</div>
                <div className="text-[10px] uppercase tracking-wide text-faint">{m.kind}</div>
              </div>
              <button
                onClick={() => remove(m.key)}
                className="text-faint opacity-0 transition hover:text-danger group-hover:opacity-100"
                aria-label="Remove"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Skeleton({ rows }: { rows: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="skeleton h-14 rounded-xl" />
      ))}
    </div>
  );
}

function Empty({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="flex flex-col items-center gap-2 px-6 py-12 text-center text-xs text-faint">
      <span className="text-faint">{icon}</span>
      {text}
    </div>
  );
}
