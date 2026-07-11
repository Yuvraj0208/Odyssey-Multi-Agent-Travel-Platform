"use client";

import { useEffect, useState } from "react";
import { createSession, getAgents, getSessionState } from "@/lib/api";
import { useStore } from "@/lib/store";
import { Header } from "./Header";
import { ChatPanel } from "./ChatPanel";
import { MapCanvas } from "./MapCanvas";
import { ItineraryTimeline } from "./ItineraryTimeline";
import { AgentRail } from "./AgentRail";
import { Toaster } from "./Toaster";
import { ApprovalModal } from "./ApprovalModal";
import { LibraryPanel, type LibraryTab } from "./LibraryPanel";
import { AuthModal } from "./AuthModal";
import { useNotifications } from "@/hooks/useNotifications";
import { getAuthUser, clearAuth, type AuthUser } from "@/lib/auth";
import { PanelRightClose, PanelRightOpen } from "lucide-react";
import { cn } from "@/lib/utils";

const SESSION_KEY = "odyssey-session";

export function Workspace() {
  const { setSession, setAgents, hydrate, reset } = useStore();
  const [ready, setReady] = useState(false);
  const [railOpen, setRailOpen] = useState(true);
  const [libraryTab, setLibraryTab] = useState<LibraryTab | null>(null);
  const [authOpen, setAuthOpen] = useState(false);
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  useNotifications();

  useEffect(() => {
    setAuthUser(getAuthUser());
  }, []);

  function signOut() {
    clearAuth();
    window.location.reload();
  }

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const agents = await getAgents().catch(() => []);
      if (!cancelled && agents.length) setAgents(agents);

      let sid = typeof window !== "undefined" ? localStorage.getItem(SESSION_KEY) : null;
      if (!sid) {
        sid = await createSession().catch(() => `local_${Date.now().toString(36)}`);
        localStorage.setItem(SESSION_KEY, sid);
      }
      if (cancelled) return;
      setSession(sid);
      try {
        const state = await getSessionState(sid);
        if (!cancelled && state?.exists) hydrate(state);
      } catch {
        /* fresh session */
      }
      if (!cancelled) setReady(true);
    })();
    return () => {
      cancelled = true;
    };
  }, [setSession, setAgents, hydrate]);

  async function newTrip() {
    const sid = await createSession().catch(() => `local_${Date.now().toString(36)}`);
    localStorage.setItem(SESSION_KEY, sid);
    reset();
    setSession(sid);
  }

  async function loadSession(sid: string) {
    localStorage.setItem(SESSION_KEY, sid);
    reset();
    setSession(sid);
    try {
      const state = await getSessionState(sid);
      if (state?.exists) hydrate(state);
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <Header
        onNewTrip={newTrip}
        onToggleRail={() => setRailOpen((v) => !v)}
        railOpen={railOpen}
        onOpenTrips={() => setLibraryTab("trips")}
        onOpenPreferences={() => setLibraryTab("preferences")}
        authUser={authUser}
        onOpenAuth={() => setAuthOpen(true)}
        onSignOut={signOut}
      />
      <main className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[minmax(360px,0.9fr)_1.3fr] xl:grid-cols-[minmax(380px,0.85fr)_1.35fr_minmax(300px,0.55fr)]">
        {/* Left: conversation */}
        <section className="min-h-0 border-r border-border">
          <ChatPanel ready={ready} />
        </section>

        {/* Center: map + timeline canvas */}
        <section className="hidden min-h-0 grid-rows-[1.05fr_1fr] lg:grid">
          <div className="min-h-0 border-b border-border">
            <MapCanvas />
          </div>
          <div className="min-h-0 overflow-hidden">
            <ItineraryTimeline />
          </div>
        </section>

        {/* Right: agent mission-control rail */}
        <aside
          className={cn(
            "hidden min-h-0 border-l border-border xl:block",
            railOpen ? "xl:block" : "xl:hidden",
          )}
        >
          <AgentRail />
        </aside>
      </main>

      {/* Rail toggle for the sliver where it is hidden */}
      <button
        onClick={() => setRailOpen((v) => !v)}
        className="fixed bottom-5 right-5 z-30 hidden items-center gap-2 rounded-full border border-border bg-surface px-3 py-2 text-xs text-muted shadow-lift transition hover:text-fg xl:flex"
      >
        {railOpen ? <PanelRightClose className="h-4 w-4" /> : <PanelRightOpen className="h-4 w-4" />}
        {railOpen ? "Hide agents" : "Show agents"}
      </button>

      <Toaster />
      <ApprovalModal />
      <LibraryPanel tab={libraryTab} onClose={() => setLibraryTab(null)} onLoadSession={loadSession} />
      <AuthModal open={authOpen} onClose={() => setAuthOpen(false)} onSuccess={() => window.location.reload()} />
    </div>
  );
}
