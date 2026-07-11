"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  Bed,
  Bus,
  CalendarRange,
  CloudRain,
  Coffee,
  Landmark,
  MapPin,
  Plane,
  Ticket,
  Utensils,
  Wallet,
} from "lucide-react";
import { useStore } from "@/lib/store";
import type { ItineraryItem } from "@/lib/types";
import { DAY_COLORS } from "./MapCanvas";
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
        </div>
        <div className="flex items-center gap-1.5 rounded-lg border border-border bg-surface-2 px-2.5 py-1 text-xs text-muted">
          <Wallet className="h-3.5 w-3.5 text-accent" />
          est. {currency(estTotal(itinerary), itinerary.currency)}
        </div>
      </div>

      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 py-4">
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
              </div>
              <div className="ml-3 space-y-1.5 border-l border-border pl-3">
                <AnimatePresence initial={false}>
                  {day.items.map((item) => (
                    <ItemRow
                      key={item.id}
                      item={item}
                      color={color}
                      selected={item.id === selectedItemId}
                      onSelect={() => selectItem(item.id === selectedItemId ? null : item.id)}
                    />
                  ))}
                </AnimatePresence>
                {day.items.length === 0 && <div className="py-1 text-xs text-faint">Open day</div>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ItemRow({
  item,
  color,
  selected,
  onSelect,
}: {
  item: ItineraryItem;
  color: string;
  selected: boolean;
  onSelect: () => void;
}) {
  const Icon = TYPE_ICON[item.type] ?? MapPin;
  return (
    <motion.button
      layout
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.22 }}
      onClick={onSelect}
      className={cn(
        "group flex w-full items-start gap-2.5 rounded-lg border px-2.5 py-2 text-left transition",
        selected
          ? "border-accent/50 bg-accent-soft shadow-soft"
          : "border-transparent hover:border-border hover:bg-surface-2",
      )}
    >
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
    </motion.button>
  );
}

function estTotal(itinerary: NonNullable<ReturnType<typeof useStore.getState>["itinerary"]>) {
  let sum = 0;
  for (const d of itinerary.days) for (const i of d.items) sum += i.cost_estimate || 0;
  return sum;
}
