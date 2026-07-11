"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Bed, Check, Plane, ShieldCheck, Ticket, X } from "lucide-react";
import { useStore } from "@/lib/store";
import { useChatStream } from "@/hooks/useChatStream";
import { cn, currency } from "@/lib/utils";
import type { Booking } from "@/lib/types";

const TYPE_ICON: Record<string, typeof Plane> = { flight: Plane, hotel: Bed, activity: Ticket };

export function ApprovalModal() {
  const approval = useStore((s) => s.approval);
  const streaming = useStore((s) => s.streaming);
  const { respondToApproval } = useChatStream();

  const isCancel = approval?.bookings?.some((b) => b.action === "cancel");

  return (
    <AnimatePresence>
      {approval && (
        <motion.div
          className="fixed inset-0 z-[60] grid place-items-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
          <motion.div
            initial={{ opacity: 0, y: 16, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.97 }}
            transition={{ type: "spring", stiffness: 320, damping: 28 }}
            className="relative w-full max-w-md overflow-hidden rounded-2xl border border-border bg-elevated shadow-lift"
          >
            <div className="flex items-center gap-2.5 border-b border-border px-5 py-4">
              <span className="grid h-9 w-9 place-items-center rounded-xl bg-accent-soft text-accent">
                <ShieldCheck className="h-5 w-5" />
              </span>
              <div>
                <div className="text-[15px] font-semibold">
                  {isCancel ? "Confirm cancellation" : "Approve booking"}
                </div>
                <div className="text-[11.5px] text-muted">
                  {isCancel
                    ? "This will cancel the selected booking."
                    : "Review before anything is confirmed. Nothing is charged until you approve."}
                </div>
              </div>
            </div>

            <div className="max-h-[46vh] space-y-2 overflow-y-auto px-5 py-4">
              {approval.bookings.map((b) => (
                <BookingRow key={b.id} b={b} />
              ))}
            </div>

            <div className="flex items-center justify-between border-t border-border px-5 py-3">
              <div className="text-[13px] text-muted">
                {isCancel ? "To cancel" : "Total"}
                <span className="ml-1.5 font-mono text-[15px] font-semibold text-fg">
                  {currency(approval.total, approval.currency)}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  disabled={streaming}
                  onClick={() => respondToApproval(false)}
                  className="flex items-center gap-1.5 rounded-xl border border-border px-3.5 py-2 text-[13px] font-medium text-muted transition hover:bg-surface-2 hover:text-fg disabled:opacity-50"
                >
                  <X className="h-4 w-4" /> Decline
                </button>
                <button
                  disabled={streaming}
                  onClick={() => respondToApproval(true)}
                  className={cn(
                    "flex items-center gap-1.5 rounded-xl px-4 py-2 text-[13px] font-semibold text-accent-fg transition disabled:opacity-50",
                    isCancel ? "bg-danger" : "bg-accent hover:opacity-90",
                  )}
                >
                  <Check className="h-4 w-4" /> {isCancel ? "Confirm cancel" : "Approve & book"}
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function BookingRow({ b }: { b: Booking }) {
  const Icon = TYPE_ICON[b.type] ?? Ticket;
  return (
    <div className="flex items-start gap-3 rounded-xl border border-border bg-surface px-3 py-2.5">
      <span className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-surface-2 text-accent">
        <Icon className="h-4 w-4" />
      </span>
      <div className="min-w-0 flex-1">
        <div className="truncate text-[13px] font-medium text-fg">{b.title}</div>
        <div className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[11px] text-faint">
          <span>{b.provider}</span>
          <span>-</span>
          <span>{b.cancellation}</span>
        </div>
      </div>
      <div className="font-mono text-[13px] font-semibold text-fg">
        {currency(b.price, b.currency)}
      </div>
    </div>
  );
}
