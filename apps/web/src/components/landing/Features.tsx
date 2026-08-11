"use client";

import { motion } from "framer-motion";
import { Reveal } from "./Reveal";
import {
  Bell,
  Brain,
  CloudRain,
  Footprints,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { SectionHeading } from "./AgentTheatre";

export function Features() {
  return (
    <section className="relative mx-auto max-w-6xl px-6 py-24 sm:py-32">
      <SectionHeading
        eyebrow="Why it feels different"
        title={
          <>
            The details other planners{" "}
            <span className="italic text-white">quietly skip</span>
          </>
        }
      />

      <div className="mt-14 grid gap-3 md:grid-cols-3">
        {/* Human-in-the-loop — hero tile */}
        <Tile className="md:col-span-2" delay={0}>
          <TileHead
            icon={<ShieldCheck className="h-4 w-4" />}
            tint="text-emerald-300"
            title="Nothing is booked without your yes"
            sub="The graph literally pauses. An approval card shows the item, provider, price, and cancellation terms — and waits."
          />
          <div className="mt-5 rounded-xl border border-white/10 bg-black/30 p-3.5">
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <div className="truncate text-[12.5px] font-medium text-white/90">
                  Polaris PL331 · London → Barcelona
                </div>
                <div className="text-[11px] text-white/45">Voyair · Free cancellation up to 24h</div>
              </div>
              <div className="font-mono text-[13px] font-semibold text-white">$327</div>
            </div>
            <div className="mt-3 flex items-center gap-2">
              <span className="rounded-lg border border-white/15 px-3 py-1.5 text-[11.5px] text-white/60">
                Decline
              </span>
              <span className="relative overflow-hidden rounded-lg bg-emerald-500 px-3 py-1.5 text-[11.5px] font-semibold text-black">
                Approve &amp; book
                <motion.span
                  className="absolute inset-0 bg-white/40"
                  initial={{ x: "-100%" }}
                  whileInView={{ x: "100%" }}
                  viewport={{ once: true }}
                  transition={{ duration: 1.1, delay: 0.6, ease: "easeInOut" }}
                />
              </span>
              <span className="ml-auto text-[10.5px] text-white/35">idempotent · never double-books</span>
            </div>
          </div>
        </Tile>

        <Tile delay={0.08}>
          <TileHead
            icon={<Footprints className="h-4 w-4" />}
            tint="text-sky-300"
            title="Timed to the minute"
            sub="Real walking times between every stop, so a day is actually doable."
          />
          <div className="mt-5 space-y-2">
            {[
              ["Kinkaku-ji", "4 min"],
              ["Ryoan-ji garden", "13 min"],
              ["Nishiki Market", "—"],
            ].map(([place, walk], i) => (
              <div key={place} className="flex items-center gap-2 text-[11.5px]">
                <span className="h-1.5 w-1.5 rounded-full bg-sky-300/70" />
                <span className="flex-1 truncate text-white/70">{place}</span>
                {walk !== "—" && (
                  <span className="font-mono text-[10.5px] text-white/40">↓ {walk}</span>
                )}
              </div>
            ))}
            <div className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-emerald-400/12 px-2.5 py-1 text-[10.5px] text-emerald-300">
              <Footprints className="h-3 w-3" /> 18 min on foot · walkable
            </div>
          </div>
        </Tile>

        <Tile delay={0.12}>
          <TileHead
            icon={<Brain className="h-4 w-4" />}
            tint="text-violet-300"
            title="It remembers you"
            sub="Preferences persist across sessions and shape every future trip."
          />
          <div className="mt-5 flex flex-wrap gap-1.5">
            {["vegetarian", "dislikes crowds", "loves temples", "relaxed pace", "window seats"].map(
              (f) => (
                <span
                  key={f}
                  className="rounded-full border border-violet-300/20 bg-violet-400/10 px-2.5 py-1 text-[11px] text-violet-200"
                >
                  {f}
                </span>
              ),
            )}
          </div>
        </Tile>

        <Tile className="md:col-span-2" delay={0.16}>
          <TileHead
            icon={<Bell className="h-4 w-4" />}
            tint="text-amber-300"
            title="It watches the forecast so you don't have to"
            sub="If rain moves in on a day you planned outdoors, Odyssey tells you — and re-plans in one click."
          />
          <Reveal
            delay={0.3}
            y={12}
            className="mt-5 flex items-start gap-3 rounded-xl border border-amber-300/20 bg-amber-400/[0.07] p-3.5"
          >
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-amber-400/15 text-amber-300">
              <CloudRain className="h-4 w-4" />
            </span>
            <div className="min-w-0">
              <div className="text-[12.5px] font-medium text-white/90">Weather alert for Day 3</div>
              <div className="mt-0.5 text-[11.5px] leading-relaxed text-white/55">
                Light drizzle is now forecast, which affects your outdoor plans. Want indoor
                alternatives?
              </div>
              <span className="mt-2 inline-flex items-center gap-1.5 rounded-lg bg-indigo-500 px-2.5 py-1.5 text-[11px] font-medium text-white">
                <Sparkles className="h-3 w-3" /> Ask agents to fix it
              </span>
            </div>
          </Reveal>
        </Tile>
      </div>
    </section>
  );
}

function Tile({
  children,
  className = "",
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  return (
    <Reveal
      delay={delay}
      y={24}
      className={`rounded-2xl border border-white/10 bg-gradient-to-b from-white/[0.055] to-white/[0.015] p-6 backdrop-blur-sm ${className}`}
    >
      {children}
    </Reveal>
  );
}

function TileHead({
  icon,
  tint,
  title,
  sub,
}: {
  icon: React.ReactNode;
  tint: string;
  title: string;
  sub: string;
}) {
  return (
    <>
      <span className={`grid h-9 w-9 place-items-center rounded-xl bg-white/[0.07] ${tint}`}>
        {icon}
      </span>
      <h3 className="mt-4 text-[16.5px] font-semibold tracking-tight text-white/95">{title}</h3>
      <p className="mt-1.5 text-[13px] leading-relaxed text-white/55">{sub}</p>
    </>
  );
}
