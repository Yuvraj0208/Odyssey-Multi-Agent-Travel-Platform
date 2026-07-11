"use client";

import { useRef, useState } from "react";
import { Reorder, useDragControls } from "framer-motion";
import {
  Bed,
  Bus,
  CalendarRange,
  CloudRain,
  Coffee,
  Footprints,
  GripVertical,
  Landmark,
  MapPin,
  Plane,
  RefreshCw,
  Ticket,
  TriangleAlert,
  Utensils,
  Wallet,
} from "lucide-react";
import { useStore } from "@/lib/store";
import { recheckConditions, reorderItinerary } from "@/lib/api";
import type { Itinerary, ItineraryDay as ItineraryDayT, ItineraryItem } from "@/lib/types";
import { DAY_COLORS } from "./MapCanvas";
import { BookingsPanel } from "./BookingsPanel";
import { cn, currency } from "@/lib/utils";

const TYPE_ICON: Record<string, typeof MapPin> = {
  attraction: Landmark,
  food: Utensils,
  activity: Ticket,
  transport: Bus,
  lodging: Bed,
  flight: Plane,
  free: Coffee,
};

export function ItineraryTimeline() {
  const itinerary = useStore((s) => s.itinerary);
  const selectedItemId = useStore((s) => s.selectedItemId);
  const selectItem = useStore((s) => s.selectItem);
  const setItinerary = useStore((s) => s.setItinerary);
  const sessionId = useStore((s) => s.sessionId);
  const [rechecking, setRechecking] = useState(false);
  const [revalidating, setRevalidating] = useState(false);
  const commitTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  async function recheck() {
    if (!sessionId || rechecking) return;
    setRechecking(true);
    try {
      await recheckConditions(sessionId);
    } finally {
      setTimeout(() => setRechecking(false), 600);
    }
  }

  function onDayReorder(dayNum: number, nextItems: ItineraryItem[]) {
    if (!itinerary) return;
    const next: Itinerary = {
      ...itinerary,
      days: itinerary.days.map((d) => (d.day === dayNum ? { ...d, items: nextItems } : d)),
    };
    setItinerary(next); // optimistic
    if (commitTimer.current) clearTimeout(commitTimer.current);
    commitTimer.current = setTimeout(async () => {
      if (!sessionId) return;
      setRevalidating(true);
      const revalidated = await reorderItinerary(sessionId, next);
      if (revalidated) setItinerary(revalidated); // updated transit + feasibility
      setTimeout(() => setRevalidating(false), 400);
    }, 550);
  }

  if (!itinerary || itinerary.days.length === 0) {
    return (
      <div className="flex h-full items-center justify-center px-6 text-center">
        <div className="max-w-xs text-sm text-muted">
          <CalendarRange className="mx-auto mb-2 h-5 w-5 text-faint" />
          The day-by-day timeline builds here as the Trip Planner works.
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <CalendarRange className="h-4 w-4 text-accent" />
          {itinerary.destination ?? "Itinerary"}
          <span className="text-xs font-normal text-faint">
            {itinerary.days.length} {itinerary.days.length === 1 ? "day" : "days"}
          </span>
          {revalidating && <span className="text-[10px] text-accent">re-checking timing...</span>}
        </div>
        <div className="flex items-center gap-1.5">
          <div className="flex items-center gap-1.5 rounded-lg border border-border bg-surface-2 px-2.5 py-1 text-xs text-muted">
            <Wallet className="h-3.5 w-3.5 text-accent" />
            est. {currency(estTotal(itinerary), itinerary.currency)}
          </div>
          <button
            onClick={recheck}
            disabled={rechecking}
            title="Re-check live weather against this plan"
            className="flex items-center gap-1.5 rounded-lg border border-border bg-surface-2 px-2.5 py-1 text-xs text-muted transition hover:text-fg disabled:opacity-60"
          >
            <RefreshCw className={cn("h-3.5 w-3.5 text-accent", rechecking && "animate-spin")} />
            {rechecking ? "Checking" : "Re-check"}
          </button>
        </div>
      </div>

      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 py-4">
        <BookingsPanel />
        {itinerary.days.map((day) => {
          const color = DAY_COLORS[(day.day - 1) % DAY_COLORS.length];
          return (
            <div key={day.day}>
              <div className="mb-2 flex items-center gap-2">
                <span
                  className="grid h-6 w-6 place-items-center rounded-lg text-[11px] font-bold text-white"
                  style={{ background: color }}
                >
                  {day.day}
                </span>
                <span className="text-[13px] font-semibold text-fg">Day {day.day}</span>
                {day.summary && <span className="truncate text-xs text-faint">- {day.summary}</span>}
                <DayFeasibility day={day} />
              </div>
              <Reorder.Group
                as="div"
                axis="y"
                values={day.items}
                onReorder={(next) => onDayReorder(day.day, next as ItineraryItem[])}
                className="ml-3 space-y-1.5 border-l border-border pl-3"
              >
                {day.items.map((item, i) => (
                  <ItemRow
                    key={item.id}
                    item={item}
                    color={color}
                    selected={item.id === selectedItemId}
                    isLast={i === day.items.length - 1}
                    onSelect={() => selectItem(item.id === selectedItemId ? null : item.id)}
                  />
                ))}
                {day.items.length === 0 && <div className="py-1 text-xs text-faint">Open day</div>}
              </Reorder.Group>
            </div>
          );
        })}
        <p className="px-1 text-center text-[10.5px] text-faint">
          Tip: drag stops by the handle to reorder - Logistics re-checks the timing.
        </p>
      </div>
    </div>
  );
}

function DayFeasibility({ day }: { day: ItineraryDayT }) {
  if (day.travel_min == null) return null;
  const packed = day.feasible === false;
  return (
    <span
      className={cn(
        "ml-auto inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium",
        packed ? "bg-amber-500/15 text-amber-400" : "bg-emerald-500/12 text-emerald-400",
      )}
      title={packed ? "This day involves a lot of walking" : "Comfortably walkable"}
    >
      {packed ? <TriangleAlert className="h-3 w-3" /> : <Footprints className="h-3 w-3" />}
      {Math.round(day.travel_min)} min on foot
    </span>
  );
}

function ItemRow({
  item,
  color,
  selected,
  isLast,
  onSelect,
}: {
  item: ItineraryItem;
  color: string;
  selected: boolean;
  isLast: boolean;
  onSelect: () => void;
}) {
  const Icon = TYPE_ICON[item.type] ?? MapPin;
  const controls = useDragControls();
  return (
    <Reorder.Item
      as="div"
      value={item}
      dragListener={false}
      dragControls={controls}
      className={cn(
        "group rounded-lg border transition",
        selected ? "border-accent/50 bg-accent-soft shadow-soft" : "border-transparent hover:border-border hover:bg-surface-2",
      )}
    >
      <div className="flex items-start gap-2 px-2 py-2">
        <button
          onPointerDown={(e) => controls.start(e)}
          className="mt-1 cursor-grab touch-none text-faint transition hover:text-muted active:cursor-grabbing"
          aria-label="Drag to reorder"
        >
          <GripVertical className="h-3.5 w-3.5" />
        </button>
        <button onClick={onSelect} className="flex min-w-0 flex-1 items-start gap-2.5 text-left">
          <span
            className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-md"
            style={{ background: `${color}20`, color }}
          >
            <Icon className="h-3.5 w-3.5" />
          </span>
          <span className="min-w-0 flex-1">
            <span className="flex items-center gap-2">
              {item.start && <span className="font-mono text-[11px] text-faint">{item.start}</span>}
              <span className="truncate text-[13px] font-medium text-fg">{item.title}</span>
            </span>
            {item.description && (
              <span className="mt-0.5 line-clamp-2 block text-[11.5px] leading-snug text-muted">
                {item.description}
              </span>
            )}
            <span className="mt-1 flex flex-wrap items-center gap-1.5">
              {item.geo && (
                <span className="inline-flex items-center gap-0.5 text-[10.5px] text-faint">
                  <MapPin className="h-3 w-3" /> on map
                </span>
              )}
              {typeof item.cost_estimate === "number" && item.cost_estimate > 0 && (
                <span className="rounded bg-surface-2 px-1.5 py-0.5 text-[10.5px] text-muted">
                  {currency(item.cost_estimate, item.currency)}
                </span>
              )}
              {item.weather_note && (
                <span className="inline-flex items-center gap-0.5 rounded bg-sky-500/10 px-1.5 py-0.5 text-[10.5px] text-sky-400">
                  <CloudRain className="h-3 w-3" /> {item.weather_note}
                </span>
              )}
            </span>
          </span>
        </button>
      </div>
      {item.transit_to_next_min != null && !isLast && (
        <div className="flex items-center gap-1.5 border-t border-border/60 px-3 py-1 text-[10.5px] text-faint">
          <Footprints className="h-3 w-3" />
          {Math.round(item.transit_to_next_min)} min walk to next
          {item.transit_to_next_km ? ` (${item.transit_to_next_km.toFixed(1)} km)` : ""}
        </div>
      )}
    </Reorder.Item>
  );
}

function estTotal(itinerary: NonNullable<ReturnType<typeof useStore.getState>["itinerary"]>) {
  let sum = 0;
  for (const d of itinerary.days) for (const i of d.items) sum += i.cost_estimate || 0;
  return sum;
}
