"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useStore } from "@/lib/store";
import { agentMeta } from "./agentMeta";
import { cn } from "@/lib/utils";
import type { AgentStatus } from "@/lib/types";

const W = 280;
const SUPER = "supervisor";

interface Pos {
  x: number;
  y: number;
}

function layout(specialists: string[]): { pos: Record<string, Pos>; H: number } {
  const pos: Record<string, Pos> = { [SUPER]: { x: W / 2, y: 40 } };
  const cols = 2;
  specialists.forEach((name, i) => {
    const row = Math.floor(i / cols);
    const col = i % cols;
    pos[name] = { x: col === 0 ? W * 0.24 : W * 0.76, y: 130 + row * 82 };
  });
  const rows = Math.ceil(specialists.length / cols) || 1;
  return { pos, H: 130 + rows * 82 };
}

export function MissionControlGraph() {
  const agents = useStore((s) => s.agents);
  const status = useStore((s) => s.agentStatus);
  const handoffs = useStore((s) => s.handoffs);

  const specialists = agents.filter((a) => a.name !== SUPER).map((a) => a.name);
  const { pos, H } = layout(specialists);

  // Animate the most recent handoff edge (a dot travels from source to target).
  const [pulse, setPulse] = useState<{ id: string; from: string; to: string } | null>(null);
  const latest = handoffs[0];
  useEffect(() => {
    if (!latest) return;
    setPulse({ id: latest.id, from: latest.from, to: latest.to });
    const t = setTimeout(() => setPulse((p) => (p?.id === latest.id ? null : p)), 1500);
    return () => clearTimeout(t);
  }, [latest?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (agents.length === 0) {
    return <div className="px-1 py-6 text-center text-xs text-faint">Loading agent team...</div>;
  }

  return (
    <div className="relative w-full" style={{ aspectRatio: `${W} / ${H}` }}>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="absolute inset-0 h-full w-full"
        preserveAspectRatio="xMidYMid meet"
      >
        {/* connectors from supervisor to each specialist */}
        {specialists.map((name) => {
          const a = pos[SUPER];
          const b = pos[name];
          const active =
            status[name] === "active" ||
            (pulse && (pulse.to === name || pulse.from === name));
          return (
            <line
              key={name}
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              stroke={active ? "rgb(var(--accent))" : "rgb(var(--border-strong))"}
              strokeWidth={active ? 1.6 : 1}
              strokeOpacity={active ? 0.9 : 0.4}
              className="transition-all duration-300"
            />
          );
        })}
        {/* traveling handoff pulse */}
        {pulse && pos[pulse.from] && pos[pulse.to] && (
          <circle key={pulse.id} r={3.5} fill="rgb(var(--accent))">
            <animateMotion
              dur="1.2s"
              repeatCount="1"
              path={`M${pos[pulse.from].x} ${pos[pulse.from].y} L${pos[pulse.to].x} ${pos[pulse.to].y}`}
            />
          </circle>
        )}
      </svg>

      {/* nodes (HTML for crisp icons + labels), positioned in the same coord space */}
      {[SUPER, ...specialists].map((name) => (
        <Node key={name} name={name} status={status[name] ?? "idle"} pos={pos[name]} H={H} isSuper={name === SUPER} />
      ))}
    </div>
  );
}

function Node({
  name,
  status,
  pos,
  H,
  isSuper,
}: {
  name: string;
  status: AgentStatus;
  pos: Pos;
  H: number;
  isSuper: boolean;
}) {
  const meta = agentMeta(name);
  const Icon = meta.Icon;
  const active = status === "active";
  const done = status === "done";
  const error = status === "error";
  return (
    <div
      className="absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-1"
      style={{ left: `${(pos.x / W) * 100}%`, top: `${(pos.y / H) * 100}%`, width: 84 }}
    >
      <motion.div
        animate={active ? { scale: [1, 1.08, 1] } : { scale: 1 }}
        transition={active ? { repeat: Infinity, duration: 1.6 } : { duration: 0.2 }}
        className={cn(
          "relative grid place-items-center rounded-2xl border transition-colors",
          isSuper ? "h-11 w-11" : "h-10 w-10",
          active
            ? cn("border-transparent ring-2", meta.ring, meta.bg)
            : done
              ? "border-border bg-surface"
              : error
                ? "border-danger/50 bg-danger/10"
                : "border-border bg-surface-2",
        )}
      >
        <Icon className={cn(isSuper ? "h-5 w-5" : "h-[18px] w-[18px]", active || done ? meta.text : "text-faint")} />
        {active && (
          <span className={cn("absolute -right-0.5 -top-0.5 h-2.5 w-2.5 animate-ping rounded-full", meta.dot)} />
        )}
        {done && (
          <span className="absolute -right-1 -top-1 grid h-3.5 w-3.5 place-items-center rounded-full bg-success text-[8px] text-white">
            ✓
          </span>
        )}
      </motion.div>
      <span
        className={cn(
          "max-w-full truncate text-center text-[9.5px] font-medium leading-tight",
          active ? meta.text : "text-faint",
        )}
      >
        {meta.label}
      </span>
    </div>
  );
}
