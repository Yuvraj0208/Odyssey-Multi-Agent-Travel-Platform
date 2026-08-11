"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Brain,
  Compass,
  Github,
  Globe2,
  LifeBuoy,
  Map as MapIcon,
  Route,
  Ticket,
} from "lucide-react";
import { asset } from "@/lib/asset";
import { SectionHeading } from "./AgentTheatre";

const REPO = "https://github.com/Yuvraj0208/Odyssey-Multi-Agent-Travel-Platform";

const ROSTER = [
  { Icon: Compass, name: "Supervisor", role: "Reads intent, routes the team, decides when you're done", tint: "text-indigo-300" },
  { Icon: Brain, name: "Memory", role: "Recalls how you like to travel and personalizes the plan", tint: "text-violet-300" },
  { Icon: Globe2, name: "Destination Intelligence", role: "Live weather, real points of interest, local context", tint: "text-teal-300" },
  { Icon: MapIcon, name: "Trip Planner", role: "Turns research into a day-by-day plan you'd actually follow", tint: "text-amber-300" },
  { Icon: Route, name: "Logistics", role: "Times every walk, flags days that are too packed", tint: "text-sky-300" },
  { Icon: Ticket, name: "Booking", role: "Prices flights, hotels, activities — and waits for your approval", tint: "text-emerald-300" },
  { Icon: LifeBuoy, name: "Traveler Support", role: "Answers questions and handles changes, day or night", tint: "text-rose-300" },
];

const STACK = [
  "LangGraph", "FastAPI", "Next.js 15", "React 19", "Postgres", "Redis",
  "Qdrant", "MapLibre", "Open-Meteo", "OpenStreetMap", "OSRM", "Langfuse",
];

const CREDITS = [
  ["Amalfi Coast", "Bruno Rijsman", "CC BY-SA 2.0"],
  ["Kyoto", "Nacaru", "CC BY-SA 4.0"],
  ["Santorini", "TomasEE", "CC BY 3.0"],
  ["Marrakesh", "Boris Macek", "CC BY-SA 3.0"],
  ["Machu Picchu", "Draceane", "CC BY-SA 4.0"],
  ["Kerala", "Saad Faruque", "CC BY-SA 2.0"],
  ["Bali", "Grayswoodsurrey", "CC BY-SA 4.0"],
];

export function AgentRoster() {
  return (
    <section id="agents" className="relative mx-auto max-w-6xl px-6 py-24 sm:py-32">
      <SectionHeading
        eyebrow="Meet the team"
        title={
          <>
            Seven specialists, one{" "}
            <span className="italic text-white">shared brain</span>
          </>
        }
        sub="Each agent owns one job and hands off with a reason. Adding an eighth takes one file — the supervisor discovers it automatically."
      />

      <div className="mt-14 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {ROSTER.map(({ Icon, name, role, tint }, i) => (
          <motion.div
            key={name}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.6, delay: (i % 3) * 0.07, ease: [0.22, 1, 0.36, 1] }}
            className="group relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] p-5 transition-colors hover:border-white/20 hover:bg-white/[0.06]"
          >
            <span className={`grid h-9 w-9 place-items-center rounded-xl bg-white/[0.07] ${tint}`}>
              <Icon className="h-4 w-4" />
            </span>
            <h3 className="mt-4 text-[15px] font-semibold tracking-tight text-white/95">{name}</h3>
            <p className="mt-1.5 text-[12.5px] leading-relaxed text-white/50">{role}</p>
            <span className="pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full bg-white/[0.05] opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-100" />
          </motion.div>
        ))}
      </div>
    </section>
  );
}

export function FinalCTA() {
  return (
    <section className="relative isolate overflow-hidden">
      <div className="absolute inset-0 -z-20">
        <img
          src={asset("/destinations/kyoto.jpg")}
          alt="Kinkaku-ji reflected in still water, Kyoto"
          loading="lazy"
          className="h-full w-full scale-105 object-cover"
        />
      </div>
      <div className="absolute inset-0 -z-10 bg-[rgb(9,11,16)]/80" />
      <div className="absolute inset-0 -z-10 bg-gradient-to-b from-[rgb(9,11,16)] via-transparent to-[rgb(9,11,16)]" />

      <div className="mx-auto max-w-3xl px-6 py-28 text-center sm:py-36">
        <motion.h2
          initial={{ opacity: 0, y: 22 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="text-balance font-display text-[clamp(2.1rem,5.5vw,3.6rem)] font-medium leading-[1.05] tracking-[-0.02em] text-white"
        >
          Tell it where you're dreaming of.
          <br />
          <span className="italic text-white/70">Watch the team get to work.</span>
        </motion.h2>
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.12 }}
          className="mt-9 flex flex-wrap items-center justify-center gap-3"
        >
          <Link
            href="/app"
            className="group inline-flex items-center gap-2 rounded-full bg-white px-7 py-3.5 text-[15px] font-semibold text-neutral-900 transition hover:scale-[1.02]"
          >
            Open Odyssey
            <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
          </Link>
          <a
            href={REPO}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/[0.06] px-7 py-3.5 text-[15px] font-medium text-white backdrop-blur-md transition hover:bg-white/[0.12]"
          >
            <Github className="h-4 w-4" /> Star on GitHub
          </a>
        </motion.div>
        <p className="mt-6 text-[12.5px] text-white/40">
          Free and open source · runs locally · bring your own model
        </p>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer id="tech" className="border-t border-white/10 bg-[rgb(9,11,16)]">
      <div className="mx-auto max-w-6xl px-6 py-14">
        <div className="flex flex-wrap justify-center gap-2">
          {STACK.map((s) => (
            <span
              key={s}
              className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[11.5px] text-white/55"
            >
              {s}
            </span>
          ))}
        </div>

        <div className="mt-12 flex flex-col items-center gap-4 border-t border-white/[0.07] pt-8 text-center">
          <div className="flex items-center gap-2.5">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-white/10 text-white">
              <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
                <circle cx="12" cy="12" r="9" />
                <path d="m15.5 8.5-2 5-5 2 2-5z" fill="currentColor" stroke="none" />
              </svg>
            </span>
            <span className="font-display text-[17px] text-white">Odyssey</span>
          </div>
          <p className="max-w-md text-[12px] leading-relaxed text-white/40">
            An open-source multi-agent travel platform. Built with LangGraph, grounded in open
            tourism data, and released under the MIT license.
          </p>
          <div className="flex items-center gap-5 text-[12.5px] text-white/50">
            <a href={REPO} target="_blank" rel="noreferrer" className="transition hover:text-white">
              GitHub
            </a>
            <Link href="/app" className="transition hover:text-white">
              Open app
            </Link>
            <a
              href={`${REPO}#-architecture`}
              target="_blank"
              rel="noreferrer"
              className="transition hover:text-white"
            >
              Architecture
            </a>
          </div>

          <details className="mt-4 w-full max-w-xl text-left">
            <summary className="cursor-pointer text-center text-[11px] text-white/30 transition hover:text-white/50">
              Photography credits
            </summary>
            <ul className="mt-3 space-y-1 text-[10.5px] leading-relaxed text-white/30">
              {CREDITS.map(([place, author, license]) => (
                <li key={place}>
                  {place} — {author}, {license}, via Wikimedia Commons
                </li>
              ))}
            </ul>
          </details>
        </div>
      </div>
    </footer>
  );
}
