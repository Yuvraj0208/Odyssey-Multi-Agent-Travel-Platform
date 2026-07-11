import {
  Brain,
  Compass,
  Globe2,
  LifeBuoy,
  Map,
  Route,
  Ticket,
  type LucideIcon,
} from "lucide-react";

export interface AgentMeta {
  label: string;
  Icon: LucideIcon;
  // tailwind color tokens (fixed palette so agents are visually distinct)
  text: string;
  bg: string;
  ring: string;
  dot: string;
}

const META: Record<string, AgentMeta> = {
  supervisor: { label: "Supervisor", Icon: Compass, text: "text-indigo-400", bg: "bg-indigo-500/12", ring: "ring-indigo-500/40", dot: "bg-indigo-400" },
  destination_intelligence: { label: "Destination Intel", Icon: Globe2, text: "text-teal-400", bg: "bg-teal-500/12", ring: "ring-teal-500/40", dot: "bg-teal-400" },
  trip_planner: { label: "Trip Planner", Icon: Map, text: "text-amber-400", bg: "bg-amber-500/12", ring: "ring-amber-500/40", dot: "bg-amber-400" },
  logistics: { label: "Logistics", Icon: Route, text: "text-sky-400", bg: "bg-sky-500/12", ring: "ring-sky-500/40", dot: "bg-sky-400" },
  memory: { label: "Memory", Icon: Brain, text: "text-violet-400", bg: "bg-violet-500/12", ring: "ring-violet-500/40", dot: "bg-violet-400" },
  booking: { label: "Booking", Icon: Ticket, text: "text-emerald-400", bg: "bg-emerald-500/12", ring: "ring-emerald-500/40", dot: "bg-emerald-400" },
  support: { label: "Traveler Support", Icon: LifeBuoy, text: "text-rose-400", bg: "bg-rose-500/12", ring: "ring-rose-500/40", dot: "bg-rose-400" },
};

const FALLBACK: AgentMeta = {
  label: "Assistant",
  Icon: Compass,
  text: "text-muted",
  bg: "bg-surface-2",
  ring: "ring-border",
  dot: "bg-muted",
};

export function agentMeta(name?: string | null): AgentMeta {
  if (!name) return FALLBACK;
  return META[name] ?? { ...FALLBACK, label: name.replace(/_/g, " ") };
}
