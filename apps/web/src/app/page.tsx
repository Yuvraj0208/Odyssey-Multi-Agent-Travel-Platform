import { Hero } from "@/components/landing/Hero";
import { AgentTheatre } from "@/components/landing/AgentTheatre";
import { Features } from "@/components/landing/Features";
import { Destinations } from "@/components/landing/Destinations";
import { AgentRoster, FinalCTA, Footer } from "@/components/landing/Closing";
import { StatBand } from "@/components/landing/StatBand";

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-[rgb(9,11,16)]">
      <Hero />
      <StatBand />
      <AgentTheatre />
      <Features />
      <Destinations />
      <AgentRoster />
      <FinalCTA />
      <Footer />
    </main>
  );
}
