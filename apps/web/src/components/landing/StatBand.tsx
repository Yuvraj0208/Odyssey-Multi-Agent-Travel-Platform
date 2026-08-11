"use client";

import { Reveal } from "./Reveal";

const STATS = [
  { value: "7", label: "specialized agents", sub: "collaborating live" },
  { value: "0", label: "invented places", sub: "every venue is real" },
  { value: "100%", label: "open source", sub: "MIT, runs locally" },
  { value: "1 click", label: "to approve", sub: "nothing books itself" },
];

export function StatBand() {
  return (
    <section className="relative border-y border-white/[0.07] bg-white/[0.02]">
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-y-8 px-6 py-12 sm:py-14 lg:grid-cols-4">
        {STATS.map((s, i) => (
          <Reveal key={s.label} delay={i * 0.08} y={14} className="text-center">
            <div className="font-display text-[clamp(1.9rem,4vw,2.6rem)] font-medium leading-none text-white">
              {s.value}
            </div>
            <div className="mt-2 text-[12.5px] font-medium text-white/70">{s.label}</div>
            <div className="text-[11px] text-white/35">{s.sub}</div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
