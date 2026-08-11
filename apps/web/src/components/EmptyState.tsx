"use client";

import { motion } from "framer-motion";
import { ArrowRight, Compass, Globe2, Loader2, Map, PlugZap } from "lucide-react";
import { useChatStream } from "@/hooks/useChatStream";
import type { BackendState } from "./Workspace";

const EXAMPLES = [
  "Plan a relaxed 3-day trip to Kyoto in April. I love temples, gardens, and great food. Mid-range budget.",
  "4 days in Lisbon for two, foodie and history focused, walkable neighborhoods, early May.",
  "A packed long weekend in Barcelona - architecture, tapas, and the beach. Late September.",
];

export function EmptyState({ ready, backend }: { ready: boolean; backend: BackendState }) {
  const { send } = useChatStream();

  return (
    <div className="flex h-full flex-col items-center justify-center px-6 py-10">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-xl text-center"
      >
        <div className="mx-auto mb-5 grid h-14 w-14 place-items-center rounded-2xl bg-accent text-accent-fg shadow-glow">
          <Compass className="h-7 w-7" />
        </div>
        <h1 className="text-balance text-2xl font-semibold tracking-tight text-fg sm:text-[26px]">
          Where to next?
        </h1>
        <p className="mx-auto mt-2 max-w-md text-pretty text-sm leading-relaxed text-muted">
          Describe your trip and watch a team of specialized agents research it, plan it, and lay it
          out on a live map - grounded in real weather and places.
        </p>

        <div className="mt-6 flex flex-col gap-2">
          {EXAMPLES.map((ex, i) => (
            <motion.button
              key={i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 + i * 0.07 }}
              disabled={!ready}
              onClick={() => send(ex)}
              className="group flex items-center gap-3 rounded-xl border border-border bg-surface px-4 py-3 text-left text-[13px] text-fg shadow-soft transition hover:border-accent/40 hover:bg-surface-2 disabled:opacity-50"
            >
              <span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-accent-soft text-accent">
                {i === 0 ? <Globe2 className="h-4 w-4" /> : i === 1 ? <Map className="h-4 w-4" /> : <Compass className="h-4 w-4" />}
              </span>
              <span className="flex-1 leading-snug text-muted group-hover:text-fg">{ex}</span>
              <ArrowRight className="h-4 w-4 shrink-0 text-faint transition group-hover:translate-x-0.5 group-hover:text-accent" />
            </motion.button>
          ))}
        </div>

        <BackendNotice ready={ready} backend={backend} />
      </motion.div>
    </div>
  );
}

function BackendNotice({ ready, backend }: { ready: boolean; backend: BackendState }) {
  if (backend === "waking") {
    return (
      <div className="mx-auto mt-6 flex max-w-sm items-start gap-2.5 rounded-xl border border-warning/25 bg-warning/[0.08] px-3.5 py-3 text-left">
        <Loader2 className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-warning" />
        <div className="text-[12px] leading-relaxed text-muted">
          <span className="font-medium text-fg">Waking the agents up.</span> The demo backend
          sleeps when idle, so the first visit takes up to a minute. Hang tight.
        </div>
      </div>
    );
  }
  if (backend === "offline") {
    return (
      <div className="mx-auto mt-6 flex max-w-sm items-start gap-2.5 rounded-xl border border-danger/25 bg-danger/[0.08] px-3.5 py-3 text-left">
        <PlugZap className="mt-0.5 h-4 w-4 shrink-0 text-danger" />
        <div className="text-[12px] leading-relaxed text-muted">
          <span className="font-medium text-fg">Backend unreachable.</span> Reload to retry, or run
          it locally with <code className="rounded bg-surface-2 px-1">docker compose up</code>.
        </div>
      </div>
    );
  }
  return (
    <div className="mt-6 flex items-center justify-center gap-2 text-[11px] text-faint">
      <span className={`h-1.5 w-1.5 rounded-full ${ready ? "bg-success" : "bg-warning animate-pulse"}`} />
      {ready ? "Agents ready" : "Connecting to the agent team..."}
    </div>
  );
}
