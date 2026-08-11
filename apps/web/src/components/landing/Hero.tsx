"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Github, MapPin, Sparkles } from "lucide-react";
import { asset } from "@/lib/asset";

const REPO = "https://github.com/Yuvraj0208/Odyssey-Multi-Agent-Travel-Platform";

const rise = {
  hidden: { opacity: 0, y: 24 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: 0.15 + i * 0.09, duration: 0.8, ease: [0.22, 1, 0.36, 1] as const },
  }),
};

export function Hero() {
  return (
    <section className="relative isolate flex min-h-[100svh] flex-col overflow-hidden">
      {/* Cinematic backdrop */}
      <div className="absolute inset-0 -z-20">
        <img
          src={asset("/destinations/amalfi.jpg")}
          alt="The Amalfi Coast at golden hour"
          className="h-full w-full animate-kenburns object-cover"
          fetchPriority="high"
        />
      </div>
      {/* Legibility + mood gradients */}
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(120%_90%_at_70%_10%,transparent_0%,rgba(6,8,15,0.55)_45%,rgba(6,8,15,0.92)_100%)]" />
      <div className="absolute inset-0 -z-10 bg-gradient-to-b from-[rgba(6,8,15,0.75)] via-transparent to-[rgb(9,11,16)]" />
      {/* Aurora accent wash */}
      <div className="pointer-events-none absolute -left-40 top-10 -z-10 h-[38rem] w-[38rem] animate-aurora rounded-full bg-indigo-500/25 blur-[130px]" />
      <div className="pointer-events-none absolute -right-32 top-1/3 -z-10 h-[32rem] w-[32rem] animate-aurora rounded-full bg-teal-400/20 blur-[130px] [animation-delay:-8s]" />

      <Nav />

      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col justify-center px-6 pb-12 pt-6">
        <motion.div initial="hidden" animate="show" className="max-w-3xl">
          <motion.div variants={rise} custom={0}>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/[0.07] px-3.5 py-1.5 text-[12px] font-medium text-white/80 backdrop-blur-md">
              <Sparkles className="h-3.5 w-3.5 text-amber-300" />
              Seven specialized agents. One itinerary.
            </span>
          </motion.div>

          <motion.h1
            variants={rise}
            custom={1}
            className="mt-5 text-balance font-display text-[clamp(2.5rem,6.2vw,4.5rem)] font-medium leading-[1] tracking-[-0.02em] text-white"
          >
            Your next journey,
            <br />
            planned by a{" "}
            <span className="bg-gradient-to-r from-amber-200 via-rose-200 to-teal-200 bg-clip-text italic text-transparent">
              team of agents
            </span>
          </motion.h1>

          <motion.p
            variants={rise}
            custom={2}
            className="mt-5 max-w-xl text-pretty text-[16.5px] leading-relaxed text-white/70"
          >
            Describe a trip in plain English. Watch a supervisor route work to specialists that
            check live weather, find real places, time every walk between stops, and price your
            flights and hotels — all in front of you, all under your approval.
          </motion.p>

          <motion.div variants={rise} custom={3} className="mt-8 flex flex-wrap items-center gap-3">
            <Link
              href="/app"
              className="group inline-flex items-center gap-2 rounded-full bg-white px-6 py-3.5 text-[14.5px] font-semibold text-neutral-900 shadow-[0_8px_30px_rgba(0,0,0,0.35)] transition hover:scale-[1.02] hover:shadow-[0_10px_40px_rgba(255,255,255,0.25)]"
            >
              Start planning free
              <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
            </Link>
            <a
              href={REPO}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/[0.06] px-6 py-3.5 text-[14.5px] font-medium text-white backdrop-blur-md transition hover:bg-white/[0.12]"
            >
              <Github className="h-4 w-4" />
              View the source
            </a>
          </motion.div>

          <motion.div
            variants={rise}
            custom={4}
            className="mt-8 flex flex-wrap items-center gap-x-8 gap-y-2.5 text-[12.5px] text-white/55"
          >
            {[
              "Live weather + real places",
              "Nothing booked without your yes",
              "Remembers how you travel",
            ].map((t) => (
              <span key={t} className="flex items-center gap-2">
                <span className="h-1 w-1 rounded-full bg-teal-300" />
                {t}
              </span>
            ))}
          </motion.div>
        </motion.div>
      </div>

      {/* Location credit + scroll hint */}
      <div className="relative z-10 mx-auto mb-6 flex w-full max-w-6xl items-end justify-between px-6">
        <span className="flex items-center gap-1.5 text-[11px] uppercase tracking-[0.18em] text-white/40">
          <MapPin className="h-3 w-3" /> Amalfi Coast, Italy
        </span>
        <span className="hidden h-9 w-5 items-start justify-center rounded-full border border-white/25 pt-1.5 sm:flex">
          <span className="h-1.5 w-1 animate-scroll-hint rounded-full bg-white/70" />
        </span>
      </div>
    </section>
  );
}

function Nav() {
  return (
    <header className="relative z-20 mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
      <div className="flex items-center gap-2.5">
        <span className="grid h-9 w-9 place-items-center rounded-xl bg-white/10 text-white backdrop-blur-md ring-1 ring-white/20">
          <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
            <circle cx="12" cy="12" r="9" />
            <path d="m15.5 8.5-2 5-5 2 2-5z" fill="currentColor" stroke="none" />
          </svg>
        </span>
        <span className="font-display text-[19px] font-medium tracking-tight text-white">Odyssey</span>
      </div>
      <nav className="hidden items-center gap-8 text-[13.5px] text-white/70 md:flex">
        {[
          ["How it works", "#how"],
          ["The team", "#agents"],
          ["Destinations", "#destinations"],
          ["Tech", "#tech"],
        ].map(([label, href]) => (
          <a key={href} href={href} className="transition hover:text-white">
            {label}
          </a>
        ))}
      </nav>
      <Link
        href="/app"
        className="rounded-full border border-white/20 bg-white/[0.08] px-4 py-2 text-[13px] font-medium text-white backdrop-blur-md transition hover:bg-white/[0.16]"
      >
        Open app
      </Link>
    </header>
  );
}
