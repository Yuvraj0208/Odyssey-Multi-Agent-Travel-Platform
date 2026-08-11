"use client";

import Link from "next/link";
import { Reveal } from "./Reveal";
import { ArrowUpRight } from "lucide-react";
import { asset } from "@/lib/asset";
import { SectionHeading } from "./AgentTheatre";

const PLACES = [
  {
    slug: "kyoto",
    name: "Kyoto",
    country: "Japan",
    blurb: "Temple mornings, garden afternoons",
    span: "sm:col-span-2 sm:row-span-2",
  },
  { slug: "santorini", name: "Santorini", country: "Greece", blurb: "Caldera sunsets", span: "" },
  { slug: "marrakesh", name: "Marrakesh", country: "Morocco", blurb: "Souks and courtyards", span: "" },
  {
    slug: "machupicchu",
    name: "Machu Picchu",
    country: "Peru",
    blurb: "The classic ascent",
    span: "sm:col-span-2",
  },
  { slug: "kerala", name: "Kerala", country: "India", blurb: "Backwaters, slowly", span: "" },
  { slug: "bali", name: "Bali", country: "Indonesia", blurb: "Sea temples at dusk", span: "" },
];

export function Destinations() {
  return (
    <section id="destinations" className="relative mx-auto max-w-6xl px-6 py-24 sm:py-32">
      <SectionHeading
        eyebrow="Anywhere you're curious about"
        title={
          <>
            Real places, pulled from{" "}
            <span className="italic text-white">open map data</span>
          </>
        }
        sub="Odyssey never invents a venue. Every stop it suggests exists on OpenStreetMap, with coordinates that land correctly on your map."
      />

      <div className="mt-14 grid auto-rows-[190px] grid-cols-1 gap-3 sm:grid-cols-4">
        {PLACES.map((p, i) => (
          <Reveal
            key={p.slug}
            delay={(i % 3) * 0.08}
            y={26}
            className={`group relative overflow-hidden rounded-2xl border border-white/10 ${p.span}`}
          >
            <img
              src={asset(`/destinations/${p.slug}.jpg`)}
              alt={`${p.name}, ${p.country}`}
              loading="lazy"
              className="absolute inset-0 h-full w-full object-cover transition-transform duration-[1.2s] ease-out group-hover:scale-[1.08]"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/25 to-transparent transition-opacity duration-500 group-hover:from-black/90" />
            <div className="absolute inset-x-0 bottom-0 p-4">
              <div className="flex items-end justify-between gap-2">
                <div>
                  <div className="text-[10px] uppercase tracking-[0.18em] text-white/50">
                    {p.country}
                  </div>
                  <div className="font-display text-[22px] font-medium leading-tight text-white">
                    {p.name}
                  </div>
                  <div className="mt-0.5 text-[12px] text-white/60 opacity-0 transition-all duration-500 group-hover:opacity-100">
                    {p.blurb}
                  </div>
                </div>
                <span className="grid h-8 w-8 shrink-0 translate-y-2 place-items-center rounded-full bg-white/15 text-white opacity-0 backdrop-blur-md transition-all duration-500 group-hover:translate-y-0 group-hover:opacity-100">
                  <ArrowUpRight className="h-4 w-4" />
                </span>
              </div>
            </div>
          </Reveal>
        ))}
      </div>

      <Reveal className="mt-10 text-center">
        <Link
          href="/app"
          className="group inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/[0.05] px-6 py-3 text-[14px] font-medium text-white transition hover:bg-white/[0.1]"
        >
          Plan any of these in about a minute
          <ArrowUpRight className="h-4 w-4 transition group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
        </Link>
      </Reveal>
    </section>
  );
}
