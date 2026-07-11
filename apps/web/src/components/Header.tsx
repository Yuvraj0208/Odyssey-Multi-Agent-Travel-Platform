"use client";

import { Clock, Coins, Compass, LogIn, LogOut, Plus, SlidersHorizontal, Sparkles, Zap } from "lucide-react";
import { useStore } from "@/lib/store";
import { ThemeToggle } from "./ThemeToggle";
import { NotificationBell } from "./NotificationBell";
import type { AuthUser } from "@/lib/auth";
import { cn, initials } from "@/lib/utils";

export function Header({
  onNewTrip,
  onToggleRail,
  railOpen,
  onOpenTrips,
  onOpenPreferences,
  authUser,
  onOpenAuth,
  onSignOut,
}: {
  onNewTrip: () => void;
  onToggleRail: () => void;
  railOpen: boolean;
  onOpenTrips: () => void;
  onOpenPreferences: () => void;
  authUser: AuthUser | null;
  onOpenAuth: () => void;
  onSignOut: () => void;
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
          onClick={onOpenTrips}
          title="Trips history"
          className="hidden h-9 w-9 place-items-center rounded-lg border border-border text-muted transition hover:bg-surface-2 hover:text-fg sm:grid"
        >
          <Clock className="h-4 w-4" />
        </button>
        <button
          onClick={onOpenPreferences}
          title="Preferences"
          className="hidden h-9 w-9 place-items-center rounded-lg border border-border text-muted transition hover:bg-surface-2 hover:text-fg sm:grid"
        >
          <SlidersHorizontal className="h-4 w-4" />
        </button>
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
        <NotificationBell />
        <ThemeToggle />
        {authUser ? (
          <button
            onClick={onSignOut}
            title={`${authUser.email} - click to sign out`}
            className="group flex items-center gap-1.5 rounded-lg border border-border pl-1 pr-2 py-1 text-xs text-muted transition hover:text-fg"
          >
            <span className="grid h-6 w-6 place-items-center rounded-md bg-accent text-[10px] font-bold text-accent-fg">
              {initials(authUser.name || authUser.email)}
            </span>
            <LogOut className="h-3.5 w-3.5 opacity-60 transition group-hover:opacity-100" />
          </button>
        ) : (
          <button
            onClick={onOpenAuth}
            className="flex items-center gap-1.5 rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-xs font-medium text-fg transition hover:bg-elevated"
          >
            <LogIn className="h-3.5 w-3.5" /> Sign in
          </button>
        )}
      </div>
    </header>
  );
}
