"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  CircleDot,
  Coins,
  Cpu,
  Gauge,
  Loader2,
  Wrench,
  Zap,
} from "lucide-react";
import { useStore } from "@/lib/store";
import { agentMeta } from "./agentMeta";
import { cn } from "@/lib/utils";
import type { AgentStatus } from "@/lib/types";

export function AgentRail() {
  const agents = useStore((s) => s.agents);
  const status = useStore((s) => s.agentStatus);
  const tools = useStore((s) => s.tools);
  const handoffs = useStore((s) => s.handoffs);
  const telemetry = useStore((s) => s.telemetry);

  return (
    <div className="flex h-full flex-col bg-surface/40">
      <div className="flex items-center gap-2 border-b border-border px-4 py-3">
        <span className="grid h-6 w-6 place-items-center rounded-md bg-accent-soft text-accent">
          <Activity className="h-3.5 w-3.5" />
        </span>
        <div className="text-sm font-semibold">Mission Control</div>
        <span className="ml-auto text-[10px] uppercase tracking-wide text-faint">live</span>
      </div>

      {/* Agent nodes */}
      <div className="space-y-1.5 border-b border-border px-3 py-3">
        {agents.map((a) => (
          <AgentNode key={a.name} name={a.name} status={status[a.name] ?? "idle"} role={a.role} />
        ))}
        {agents.length === 0 && <div className="px-1 py-2 text-xs text-faint">Loading agent team...</div>}
      </div>

      {/* Activity feed */}
      <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
        <div className="mb-2 flex items-center gap-1.5 px-1 text-[10px] font-semibold uppercase tracking-wide text-faint">
          <Wrench className="h-3 w-3" /> Activity
        </div>
        <div className="space-y-1.5">
          <AnimatePresence initial={false}>
            {mergeFeed(tools, handoffs).map((row) =>
              row.kind === "tool" ? (
                <ToolCard key={row.id} row={row.data} />
              ) : (
                <HandoffCard key={row.id} row={row.data} />
              ),
            )}
          </AnimatePresence>
          {tools.length === 0 && handoffs.length === 0 && (
            <div className="rounded-lg border border-dashed border-border px-3 py-6 text-center text-[11px] text-faint">
              Agent handoffs and tool calls stream here in real time.
            </div>
          )}
        </div>
      </div>

      {/* Telemetry */}
      <div className="border-t border-border px-3 py-3">
        <div className="grid grid-cols-2 gap-2">
          <Stat icon={<Zap className="h-3.5 w-3.5" />} label="Tokens" value={(telemetry?.total_tokens ?? 0).toLocaleString()} />
          <Stat icon={<Coins className="h-3.5 w-3.5" />} label="Est. cost" value={`$${(telemetry?.estimated_cost_usd ?? 0).toFixed(4)}`} />
          <Stat icon={<Wrench className="h-3.5 w-3.5" />} label="Tool calls" value={String(telemetry?.tool_calls ?? 0)} />
          <Stat icon={<Gauge className="h-3.5 w-3.5" />} label="Agent steps" value={String(telemetry?.agent_steps ?? 0)} />
        </div>
        <div className="mt-2 flex items-center gap-1.5 px-1 text-[10.5px] text-faint">
          <Cpu className="h-3 w-3" /> {telemetry?.model ?? "awaiting first run"}
        </div>
      </div>
    </div>
  );
}

function AgentNode({ name, status, role }: { name: string; status: AgentStatus; role?: string }) {
  const meta = agentMeta(name);
  const Icon = meta.Icon;
  const active = status === "active";
  return (
    <div
      className={cn(
        "flex items-center gap-2.5 rounded-xl border px-2.5 py-2 transition",
        active ? cn("border-transparent ring-1", meta.ring, meta.bg) : "border-border bg-surface",
      )}
    >
      <span
        className={cn(
          "relative grid h-8 w-8 place-items-center rounded-lg",
          meta.bg,
          active && "animate-pulse-ring",
        )}
      >
        <Icon className={cn("h-4 w-4", meta.text)} />
      </span>
      <div className="min-w-0 flex-1">
        <div className="truncate text-[12.5px] font-medium text-fg">{meta.label}</div>
        <div className="text-[10px] text-faint">{role === "supervisor" ? "orchestrator" : "specialist"}</div>
      </div>
      <StatusPip status={status} />
    </div>
  );
}

function StatusPip({ status }: { status: AgentStatus }) {
  if (status === "active")
    return <Loader2 className="h-3.5 w-3.5 animate-spin text-accent" />;
  if (status === "done") return <CheckCircle2 className="h-3.5 w-3.5 text-success" />;
  if (status === "error") return <CircleDot className="h-3.5 w-3.5 text-danger" />;
  return <span className="h-2 w-2 rounded-full bg-border-strong" />;
}

function ToolCard({ row }: { row: ReturnType<typeof useStore.getState>["tools"][number] }) {
  const meta = agentMeta(row.agent);
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="rounded-lg border border-border bg-surface px-2.5 py-2"
    >
      <div className="flex items-center gap-1.5">
        <span className={cn("h-1.5 w-1.5 rounded-full", meta.dot)} />
        <span className="font-mono text-[11px] font-medium text-fg">{row.tool}</span>
        {row.running ? (
          <Loader2 className="ml-auto h-3 w-3 animate-spin text-accent" />
        ) : (
          <span className="ml-auto text-[10px] text-faint">
            {row.ok === false ? "failed" : row.durationMs ? `${Math.round(row.durationMs)}ms` : "done"}
          </span>
        )}
      </div>
      {row.argsPreview && <div className="mt-0.5 truncate text-[10.5px] text-faint">{row.argsPreview}</div>}
      {row.summary && <div className="mt-1 line-clamp-2 text-[11px] text-muted">{row.summary}</div>}
    </motion.div>
  );
}

function HandoffCard({ row }: { row: ReturnType<typeof useStore.getState>["handoffs"][number] }) {
  const from = agentMeta(row.from);
  const to = agentMeta(row.to);
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="rounded-lg border border-accent/25 bg-accent-soft/50 px-2.5 py-2"
    >
      <div className="flex items-center gap-1.5 text-[11px] font-medium">
        <span className={from.text}>{from.label}</span>
        <ArrowRight className="h-3 w-3 text-accent" />
        <span className={to.text}>{to.label}</span>
      </div>
      {row.reason && <div className="mt-0.5 text-[10.5px] italic text-muted">{row.reason}</div>}
    </motion.div>
  );
}

function Stat({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface px-2.5 py-2">
      <div className="flex items-center gap-1 text-[10px] text-faint">
        <span className="text-accent">{icon}</span> {label}
      </div>
      <div className="mt-0.5 font-mono text-[13px] font-semibold text-fg">{value}</div>
    </div>
  );
}

// Interleave tool + handoff feeds by timestamp (newest first).
function mergeFeed(
  tools: ReturnType<typeof useStore.getState>["tools"],
  handoffs: ReturnType<typeof useStore.getState>["handoffs"],
) {
  const rows = [
    ...tools.map((t) => ({ kind: "tool" as const, id: t.id, ts: t.ts, data: t })),
    ...handoffs.map((h) => ({ kind: "handoff" as const, id: h.id, ts: h.ts, data: h })),
  ];
  return rows.sort((a, b) => b.ts - a.ts).slice(0, 30);
}
