"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  Brain,
  Check,
  Compass,
  Globe2,
  Landmark,
  Map as MapIcon,
  Route,
  Utensils,
  Wrench,
} from "lucide-react";

/**
 * A replay of a real Odyssey planning turn. The beats mirror the actual agent
 * pipeline (supervisor -> memory -> destination -> planner -> logistics) and the
 * real tools those agents call, so the film matches the product.
 */

type Beat =
  | { kind: "prompt"; text: string }
  | { kind: "agent"; id: AgentId; note: string }
  | { kind: "memory"; facts: string[] }
  | { kind: "tool"; tool: string; result: string }
  | { kind: "item"; time: string; title: string; icon: "temple" | "food" | "garden" }
  | { kind: "verdict"; text: string };

type AgentId = "supervisor" | "memory" | "destination" | "planner" | "logistics";

const AGENTS: { id: AgentId; label: string; Icon: typeof Compass; tint: string }[] = [
  { id: "supervisor", label: "Supervisor", Icon: Compass, tint: "text-indigo-300" },
  { id: "memory", label: "Memory", Icon: Brain, tint: "text-violet-300" },
  { id: "destination", label: "Destination", Icon: Globe2, tint: "text-teal-300" },
  { id: "planner", label: "Planner", Icon: MapIcon, tint: "text-amber-300" },
  { id: "logistics", label: "Logistics", Icon: Route, tint: "text-sky-300" },
];

const BEATS: { beat: Beat; hold: number }[] = [
  { beat: { kind: "prompt", text: "Plan a relaxed 3-day trip to Kyoto. I love temples and gardens." }, hold: 1500 },
  { beat: { kind: "agent", id: "supervisor", note: "understanding the request" }, hold: 1100 },
  { beat: { kind: "agent", id: "memory", note: "recalling your preferences" }, hold: 700 },
  { beat: { kind: "memory", facts: ["vegetarian", "dislikes crowds", "loves temples"] }, hold: 1500 },
  { beat: { kind: "agent", id: "destination", note: "researching Kyoto" }, hold: 700 },
  { beat: { kind: "tool", tool: "geocode_place", result: "Kyoto, Japan · 35.021, 135.754" }, hold: 900 },
  { beat: { kind: "tool", tool: "get_weather", result: "3 days · light drizzle on day 2" }, hold: 1000 },
  { beat: { kind: "tool", tool: "search_pois", result: "30 real places · 27 spiritual" }, hold: 1200 },
  { beat: { kind: "agent", id: "planner", note: "building the itinerary" }, hold: 800 },
  { beat: { kind: "item", time: "09:00", title: "Kinkaku-ji, the Golden Pavilion", icon: "temple" }, hold: 600 },
  { beat: { kind: "item", time: "11:00", title: "Ryoan-ji rock garden", icon: "garden" }, hold: 600 },
  { beat: { kind: "item", time: "13:30", title: "Lunch at Nishiki Market", icon: "food" }, hold: 900 },
  { beat: { kind: "agent", id: "logistics", note: "checking every walk" }, hold: 700 },
  { beat: { kind: "tool", tool: "plan_day_route", result: "18 min on foot · comfortably walkable" }, hold: 1100 },
  { beat: { kind: "verdict", text: "Day 1 ready — grounded in live weather and real places." }, hold: 3200 },
];

const ITEM_ICON = { temple: Landmark, garden: Landmark, food: Utensils };

export function AgentTheatre() {
  const reduced = useReducedMotion();
  const [step, setStep] = useState(reduced ? BEATS.length : 0);
  const [started, setStarted] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Prefer starting the film when it scrolls into view, but never let it sit
  // frozen: if IntersectionObserver is unavailable or hasn't reported by the time
  // the section is on screen, start anyway.
  useEffect(() => {
    const el = ref.current;
    if (!el || reduced) return;

    let io: IntersectionObserver | undefined;
    if (typeof IntersectionObserver !== "undefined") {
      io = new IntersectionObserver(([e]) => e.isIntersecting && setStarted(true), {
        threshold: 0.2,
      });
      io.observe(el);
    }

    const onScroll = () => {
      const r = el.getBoundingClientRect();
      if (r.top < window.innerHeight * 0.9 && r.bottom > 0) setStarted(true);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });

    return () => {
      io?.disconnect();
      window.removeEventListener("scroll", onScroll);
    };
  }, [reduced]);

  useEffect(() => {
    if (!started || reduced) return;
    const hold = BEATS[Math.min(step, BEATS.length - 1)].hold;
    const t = setTimeout(() => setStep((s) => (s + 1 > BEATS.length ? 0 : s + 1)), hold);
    return () => clearTimeout(t);
  }, [step, started, reduced]);

  const visible = BEATS.slice(0, step + (reduced ? 0 : 1)).map((b) => b.beat);
  const activeAgent = useMemo(() => {
    for (let i = visible.length - 1; i >= 0; i--) {
      const b = visible[i];
      if (b.kind === "agent") return b.id;
    }
    return null;
  }, [visible]);
  const doneAgents = useMemo(() => {
    const seen = new Set<AgentId>();
    visible.forEach((b) => b.kind === "agent" && seen.add(b.id));
    if (activeAgent) seen.delete(activeAgent);
    return seen;
  }, [visible, activeAgent]);

  const prompt = visible.find((b) => b.kind === "prompt") as Extract<Beat, { kind: "prompt" }> | undefined;
  const memory = visible.find((b) => b.kind === "memory") as Extract<Beat, { kind: "memory" }> | undefined;
  const tools = visible.filter((b) => b.kind === "tool") as Extract<Beat, { kind: "tool" }>[];
  const items = visible.filter((b) => b.kind === "item") as Extract<Beat, { kind: "item" }>[];
  const verdict = visible.find((b) => b.kind === "verdict") as Extract<Beat, { kind: "verdict" }> | undefined;
  const note = [...visible].reverse().find((b) => b.kind === "agent") as
    | Extract<Beat, { kind: "agent" }>
    | undefined;

  return (
    <section id="how" ref={ref} className="relative mx-auto max-w-6xl px-6 py-24 sm:py-32">
      <SectionHeading
        eyebrow="Watch it think"
        title={
          <>
            Most AI trip planners hand you a wall of text.
            <br className="hidden sm:block" />{" "}
            <span className="italic text-white">Odyssey shows its work.</span>
          </>
        }
        sub="This is a real planning turn — the same agents, tools, and handoffs you'll see in the app."
      />

      <div className="mt-14 overflow-hidden rounded-2xl border border-white/10 bg-[#0b0e15] shadow-[0_30px_90px_-20px_rgba(0,0,0,0.9)]">
        {/* window chrome */}
        <div className="flex items-center gap-2 border-b border-white/10 bg-white/[0.03] px-4 py-3">
          <span className="h-2.5 w-2.5 rounded-full bg-[#ff5f57]" />
          <span className="h-2.5 w-2.5 rounded-full bg-[#febc2e]" />
          <span className="h-2.5 w-2.5 rounded-full bg-[#28c840]" />
          <span className="ml-3 font-mono text-[11px] text-white/40">odyssey — mission control</span>
          <span className="ml-auto flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-teal-300">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-teal-300" /> live
          </span>
        </div>

        <div className="grid gap-px bg-white/[0.06] lg:grid-cols-[1.15fr_0.95fr_1fr]">
          {/* Conversation */}
          <div className="min-h-[360px] space-y-3 bg-[#0b0e15] p-5">
            <ColumnLabel>Conversation</ColumnLabel>
            <AnimatePresence>
              {prompt && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="ml-auto max-w-[92%] rounded-2xl rounded-br-md bg-indigo-500 px-3.5 py-2.5 text-[12.5px] leading-relaxed text-white"
                >
                  {prompt.text}
                </motion.div>
              )}
            </AnimatePresence>

            <AnimatePresence>
              {memory && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="rounded-2xl rounded-tl-md border border-white/10 bg-white/[0.04] px-3.5 py-2.5"
                >
                  <div className="mb-1.5 flex items-center gap-1.5 text-[10.5px] font-medium text-violet-300">
                    <Brain className="h-3 w-3" /> Memory
                  </div>
                  <p className="text-[12.5px] leading-relaxed text-white/75">
                    Welcome back — I remembered how you travel:
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {memory.facts.map((f, i) => (
                      <motion.span
                        key={f}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: i * 0.12 }}
                        className="rounded-full bg-violet-400/15 px-2 py-0.5 text-[10.5px] text-violet-200"
                      >
                        {f}
                      </motion.span>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <AnimatePresence>
              {verdict && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="rounded-2xl rounded-tl-md border border-white/10 bg-white/[0.04] px-3.5 py-2.5 text-[12.5px] leading-relaxed text-white/80"
                >
                  {verdict.text}
                </motion.div>
              )}
            </AnimatePresence>

            {!verdict && note && (
              <div className="flex items-center gap-2 pl-1 text-[11.5px] text-white/45">
                <span className="flex gap-1">
                  {[0, 1, 2].map((i) => (
                    <span
                      key={i}
                      className="h-1 w-1 animate-bounce rounded-full bg-indigo-300"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </span>
                {note.note}
              </div>
            )}
          </div>

          {/* Agent graph */}
          <div className="bg-[#0b0e15] p-5">
            <ColumnLabel>Agents</ColumnLabel>
            <div className="mt-1 space-y-2">
              {AGENTS.map(({ id, label, Icon, tint }) => {
                const active = activeAgent === id;
                const done = doneAgents.has(id);
                return (
                  <div
                    key={id}
                    className={`flex items-center gap-2.5 rounded-xl border px-2.5 py-2 transition-all duration-500 ${
                      active
                        ? "border-white/25 bg-white/[0.08]"
                        : done
                          ? "border-white/10 bg-white/[0.02]"
                          : "border-transparent bg-white/[0.015] opacity-45"
                    }`}
                  >
                    <span
                      className={`relative grid h-7 w-7 place-items-center rounded-lg bg-white/[0.06] ${active ? tint : "text-white/40"}`}
                    >
                      <Icon className="h-3.5 w-3.5" />
                      {active && (
                        <motion.span
                          layoutId="agent-halo"
                          className="absolute inset-0 rounded-lg ring-2 ring-white/40"
                          transition={{ type: "spring", stiffness: 300, damping: 26 }}
                        />
                      )}
                    </span>
                    <span className={`flex-1 text-[12px] ${active ? "text-white" : "text-white/55"}`}>
                      {label}
                    </span>
                    {done && <Check className="h-3.5 w-3.5 text-emerald-400" />}
                    {active && (
                      <span className="h-1.5 w-1.5 animate-ping rounded-full bg-white/70" />
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Tools + plan */}
          <div className="space-y-3 bg-[#0b0e15] p-5">
            <ColumnLabel>Tool calls</ColumnLabel>
            <div className="space-y-1.5">
              <AnimatePresence>
                {tools.map((t) => (
                  <motion.div
                    key={t.tool}
                    initial={{ opacity: 0, x: 12 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="rounded-lg border border-white/10 bg-white/[0.03] px-2.5 py-1.5"
                  >
                    <div className="flex items-center gap-1.5">
                      <Wrench className="h-3 w-3 text-teal-300" />
                      <span className="font-mono text-[10.5px] text-white/90">{t.tool}</span>
                      <Check className="ml-auto h-3 w-3 text-emerald-400" />
                    </div>
                    <div className="mt-0.5 pl-4.5 text-[10.5px] text-white/50">{t.result}</div>
                  </motion.div>
                ))}
              </AnimatePresence>
              {tools.length === 0 && (
                <div className="rounded-lg border border-dashed border-white/10 px-3 py-5 text-center text-[10.5px] text-white/30">
                  waiting for the first call…
                </div>
              )}
            </div>

            {items.length > 0 && (
              <>
                <ColumnLabel className="pt-2">Day 1 taking shape</ColumnLabel>
                <div className="space-y-1.5">
                  <AnimatePresence>
                    {items.map((it) => {
                      const Icon = ITEM_ICON[it.icon];
                      return (
                        <motion.div
                          key={it.title}
                          initial={{ opacity: 0, y: 10, scale: 0.97 }}
                          animate={{ opacity: 1, y: 0, scale: 1 }}
                          transition={{ type: "spring", stiffness: 260, damping: 24 }}
                          className="flex items-center gap-2 rounded-lg border border-white/10 bg-gradient-to-r from-amber-400/10 to-transparent px-2.5 py-2"
                        >
                          <Icon className="h-3.5 w-3.5 shrink-0 text-amber-300" />
                          <span className="font-mono text-[10px] text-white/40">{it.time}</span>
                          <span className="truncate text-[11.5px] text-white/85">{it.title}</span>
                        </motion.div>
                      );
                    })}
                  </AnimatePresence>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

function ColumnLabel({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`text-[10px] font-semibold uppercase tracking-[0.16em] text-white/35 ${className}`}>
      {children}
    </div>
  );
}

export function SectionHeading({
  eyebrow,
  title,
  sub,
  center = true,
}: {
  eyebrow: string;
  title: React.ReactNode;
  sub?: string;
  center?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
      className={center ? "mx-auto max-w-2xl text-center" : "max-w-2xl"}
    >
      <span className="text-[11px] font-semibold uppercase tracking-[0.22em] text-teal-300/80">
        {eyebrow}
      </span>
      <h2 className="mt-4 text-balance font-display text-[clamp(1.9rem,4.2vw,3rem)] font-medium leading-[1.1] tracking-[-0.02em] text-white/90">
        {title}
      </h2>
      {sub && <p className="mt-4 text-pretty text-[15px] leading-relaxed text-white/55">{sub}</p>}
    </motion.div>
  );
}
