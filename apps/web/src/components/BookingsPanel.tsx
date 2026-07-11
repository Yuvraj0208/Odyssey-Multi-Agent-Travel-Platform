"use client";

import { motion } from "framer-motion";
import { Bed, CheckCircle2, Plane, Ticket, XCircle } from "lucide-react";
import { useStore } from "@/lib/store";
import { cn, currency } from "@/lib/utils";
import type { Booking, Offer } from "@/lib/types";

const TYPE_ICON: Record<string, typeof Plane> = { flight: Plane, hotel: Bed, activity: Ticket };

export function BookingsPanel() {
  const confirmed = useStore((s) => s.confirmedBookings);
  const options = useStore((s) => s.options);
  const approval = useStore((s) => s.approval);

  const active = confirmed.filter((b) => b.status !== "cancelled");
  const hasOptions = options && Object.values(options).some((v) => v && v.length);
  if (active.length === 0 && confirmed.length === 0 && !hasOptions) return null;

  return (
    <div className="mb-4 rounded-xl border border-border bg-surface-2/50 p-3">
      <div className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-faint">
        <Ticket className="h-3.5 w-3.5" /> Bookings
      </div>

      {confirmed.length > 0 && (
        <div className="space-y-1.5">
          {confirmed.map((b) => (
            <ConfirmedRow key={b.id} b={b} />
          ))}
        </div>
      )}

      {/* Show alternatives only while nothing is confirmed and no modal is open. */}
      {active.length === 0 && !approval && hasOptions && (
        <div className="space-y-2">
          {(["flights", "hotels", "activities"] as const).map((cat) =>
            options?.[cat]?.length ? <OptionGroup key={cat} label={cat} offers={options[cat]!} /> : null,
          )}
        </div>
      )}
    </div>
  );
}

function ConfirmedRow({ b }: { b: Booking }) {
  const Icon = TYPE_ICON[b.type] ?? Ticket;
  const cancelled = b.status === "cancelled";
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-2.5 rounded-lg border border-border bg-surface px-2.5 py-2"
    >
      <span className="grid h-7 w-7 shrink-0 place-items-center rounded-md bg-surface-2 text-accent">
        <Icon className="h-3.5 w-3.5" />
      </span>
      <div className="min-w-0 flex-1">
        <div className={cn("truncate text-[12.5px] font-medium", cancelled ? "text-faint line-through" : "text-fg")}>
          {b.title}
        </div>
        <div className="text-[10.5px] text-faint">
          {b.provider}
          {b.booking_ref ? ` - ${b.booking_ref}` : ""}
        </div>
      </div>
      <span
        className={cn(
          "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium",
          cancelled ? "bg-surface-2 text-faint" : "bg-emerald-500/12 text-emerald-400",
        )}
      >
        {cancelled ? <XCircle className="h-3 w-3" /> : <CheckCircle2 className="h-3 w-3" />}
        {cancelled ? "Cancelled" : "Confirmed"}
      </span>
    </motion.div>
  );
}

function OptionGroup({ label, offers }: { label: string; offers: Offer[] }) {
  return (
    <div>
      <div className="mb-1 text-[10.5px] font-medium capitalize text-muted">{label}</div>
      <div className="grid grid-cols-1 gap-1.5">
        {offers.slice(0, 3).map((o) => (
          <div key={o.id} className="flex items-center justify-between rounded-lg border border-border bg-surface px-2.5 py-1.5">
            <div className="min-w-0">
              <div className="truncate text-[12px] text-fg">{o.title}</div>
              <div className="text-[10px] text-faint">{o.provider}</div>
            </div>
            <div className="font-mono text-[12px] font-semibold text-fg">{currency(o.price, o.currency)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
