"use client";

import { Compass, Coins, Plus, Sparkles, Zap } from "lucide-react";
import { useStore } from "@/lib/store";
import { ThemeToggle } from "./ThemeToggle";
import { cn } from "@/lib/utils";

export function Header({
  onNewTrip,
  onToggleRail,
  railOpen,
}: {
  onNewTrip: () => void;
  onToggleRail: () => void;
  railOpen: boolean;
}) {
  const telemetry = useStore((s) => s.telemetry);
  const itinerary = useStore((s) => s.itinerary);

  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-border bg-surface/80 px-4 backdrop-blur">
      <div className="flex items-center gap-2.5">
        <div className="grid h-8 w-8 place-items-center rounded-lg bg-accent text-accent-fg shadow-glow">
          <Compass className="h-[18px] w-[18px]" />
        </div>
        <div className="leading-tight">
          <div className="flex items-center gap-1.5 text-[15px] font-semibold tracking-tight">
            Odyssey
            <span className="rounded-full border border-border px-1.5 py-0.5 text-[10px] font-medium text-faint">
              beta
            </span>
          </div>
          <div className="hidden text-[11px] text-faint sm:block">
            {itinerary?.destination ? `Planning ${itinerary.destination}` : "AI travel, planned by a team of agents"}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {telemetry && telemetry.total_tokens > 0 && (
          <div className="hidden items-center gap-3 rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-[11px] text-muted md:flex">
            <span className="flex items-center gap-1">
              <Zap className="h-3.5 w-3.5 text-accent" />
              {telemetry.total_tokens.toLocaleString()} tok
            </span>
            <span className="flex items-center gap-1">
              <Coins className="h-3.5 w-3.5 text-accent" />${telemetry.estimated_cost_usd.toFixed(4)}
            </span>
            <span className="text-faint">{telemetry.model}</span>
          </div>
        )}
        <button
          onClick={onNewTrip}
          className="flex items-center gap-1.5 rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-xs font-medium text-fg transition hover:bg-elevated"
        >
          <Plus className="h-3.5 w-3.5" /> New trip
        </button>
        <button
          onClick={onToggleRail}
          className={cn(
            "hidden h-9 items-center gap-1.5 rounded-lg border px-3 text-xs font-medium transition xl:flex",
            railOpen
              ? "border-accent/40 bg-accent-soft text-accent"
              : "border-border text-muted hover:text-fg",
          )}
        >
          <Sparkles className="h-3.5 w-3.5" /> Agents
        </button>
        <ThemeToggle />
      </div>
    </header>
  );
}
