import { create } from "zustand";
import type {
  AgentInfo,
  AgentStatus,
  ChatMessage,
  HandoffActivity,
  Itinerary,
  Telemetry,
  ToolActivity,
  UIEvent,
} from "./types";

let seq = 0;
const uid = (p: string) => `${p}_${Date.now().toString(36)}_${(seq++).toString(36)}`;

interface OdysseyState {
  sessionId: string | null;
  agents: AgentInfo[];
  messages: ChatMessage[];
  itinerary: Itinerary | null;
  agentStatus: Record<string, AgentStatus>;
  activeAgent: string | null;
  tools: ToolActivity[];
  handoffs: HandoffActivity[];
  telemetry: Telemetry | null;
  streaming: boolean;
  errorBanner: string | null;
  selectedItemId: string | null;

  // internal streaming cursor
  _streamId: string | null;
  _streamAgent: string | null;

  setSession: (id: string) => void;
  setAgents: (a: AgentInfo[]) => void;
  hydrate: (state: any) => void;
  addUserMessage: (text: string) => void;
  beginTurn: () => void;
  endTurn: () => void;
  applyEvent: (ev: UIEvent) => void;
  selectItem: (id: string | null) => void;
  reset: () => void;
}

export const useStore = create<OdysseyState>((set, get) => ({
  sessionId: null,
  agents: [],
  messages: [],
  itinerary: null,
  agentStatus: {},
  activeAgent: null,
  tools: [],
  handoffs: [],
  telemetry: null,
  streaming: false,
  errorBanner: null,
  selectedItemId: null,
  _streamId: null,
  _streamAgent: null,

  setSession: (id) => set({ sessionId: id }),
  setAgents: (a) =>
    set({
      agents: a,
      agentStatus: Object.fromEntries(a.map((x) => [x.name, "idle" as AgentStatus])),
    }),

  hydrate: (state) =>
    set((s) => ({
      messages:
        state.transcript?.map((m: any, i: number) => ({
          id: `h_${i}`,
          role: m.role,
          agent: m.agent,
          text: m.text,
        })) ?? [],
      itinerary: state.itinerary ?? null,
      telemetry: state.telemetry ?? s.telemetry,
    })),

  addUserMessage: (text) =>
    set((s) => ({ messages: [...s.messages, { id: uid("u"), role: "user", text }] })),

  beginTurn: () =>
    set((s) => ({
      streaming: true,
      errorBanner: null,
      agentStatus: Object.fromEntries(Object.keys(s.agentStatus).map((k) => [k, "idle"])),
      _streamId: null,
      _streamAgent: null,
    })),

  endTurn: () =>
    set((s) => ({
      streaming: false,
      activeAgent: null,
      _streamId: null,
      _streamAgent: null,
      messages: s.messages.map((m) => (m.streaming ? { ...m, streaming: false } : m)),
    })),

  applyEvent: (ev) => {
    const s = get();
    switch (ev.type) {
      case "session_start": {
        const roster: AgentInfo[] = ev.data.agents ?? s.agents;
        set({
          agents: roster.length ? roster : s.agents,
          agentStatus: Object.fromEntries(
            (roster.length ? roster : s.agents).map((a) => [a.name, "idle" as AgentStatus]),
          ),
        });
        break;
      }
      case "agent_enter": {
        const a = ev.agent!;
        set({
          activeAgent: a,
          agentStatus: { ...s.agentStatus, [a]: "active" },
        });
        break;
      }
      case "agent_exit": {
        const a = ev.agent!;
        set({ agentStatus: { ...s.agentStatus, [a]: s.agentStatus[a] === "error" ? "error" : "done" } });
        break;
      }
      case "token": {
        const a = ev.agent || s._streamAgent || "assistant";
        const text: string = ev.data.text || "";
        if (!text) break;
        if (s._streamId && s._streamAgent === a) {
          set({
            messages: s.messages.map((m) => (m.id === s._streamId ? { ...m, text: m.text + text } : m)),
          });
        } else {
          const id = uid("a");
          const finalized = s.messages.map((m) => (m.streaming ? { ...m, streaming: false } : m));
          set({
            messages: [...finalized, { id, role: "assistant", agent: a, text, streaming: true }],
            _streamId: id,
            _streamAgent: a,
          });
        }
        break;
      }
      case "message": {
        const a = ev.agent || null;
        const text: string = ev.data.text || "";
        if (!text) break;
        if (s._streamId && s._streamAgent === a) {
          set({
            messages: s.messages.map((m) =>
              m.id === s._streamId ? { ...m, text, streaming: false } : m,
            ),
            _streamId: null,
            _streamAgent: null,
          });
        } else {
          set({
            messages: [
              ...s.messages.map((m) => (m.streaming ? { ...m, streaming: false } : m)),
              { id: uid("a"), role: "assistant", agent: a, text },
            ],
          });
        }
        break;
      }
      case "tool_start": {
        const t: ToolActivity = {
          id: uid("t"),
          agent: ev.agent || "",
          tool: ev.data.tool || "tool",
          argsPreview: ev.data.args_preview,
          running: true,
          ts: ev.ts,
        };
        set({ tools: [t, ...s.tools].slice(0, 40) });
        break;
      }
      case "tool_end": {
        let patched = false;
        const tools = s.tools.map((t) => {
          if (!patched && t.running && t.tool === ev.data.tool && t.agent === ev.agent) {
            patched = true;
            return { ...t, running: false, summary: ev.data.summary, ok: ev.data.ok, durationMs: ev.data.duration_ms };
          }
          return t;
        });
        set({ tools });
        break;
      }
      case "handoff": {
        const h: HandoffActivity = {
          id: uid("h"),
          from: ev.data.from,
          to: ev.data.to,
          reason: ev.data.reason,
          ts: ev.ts,
        };
        set({ handoffs: [h, ...s.handoffs].slice(0, 20) });
        break;
      }
      case "plan_updated": {
        set({ itinerary: ev.data.itinerary as Itinerary });
        break;
      }
      case "telemetry": {
        set({ telemetry: ev.data as Telemetry });
        break;
      }
      case "error": {
        set({ errorBanner: ev.data.message || "Something went wrong." });
        if (ev.agent) set({ agentStatus: { ...get().agentStatus, [ev.agent]: "error" } });
        break;
      }
      case "done": {
        get().endTurn();
        break;
      }
    }
  },

  selectItem: (id) => set({ selectedItemId: id }),

  reset: () =>
    set({
      messages: [],
      itinerary: null,
      tools: [],
      handoffs: [],
      telemetry: null,
      streaming: false,
      errorBanner: null,
      selectedItemId: null,
      _streamId: null,
      _streamAgent: null,
      activeAgent: null,
    }),
}));
