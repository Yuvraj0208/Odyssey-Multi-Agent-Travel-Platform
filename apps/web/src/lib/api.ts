import type { AgentInfo, Notification, UIEvent } from "./types";

// Same-origin in the browser (Next rewrites /api -> FastAPI). Server components
// can override with NEXT_PUBLIC_API_BASE_URL.
const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "";

function userId(): string {
  if (typeof window === "undefined") return "demo-user";
  let id = localStorage.getItem("odyssey-user");
  if (!id) {
    id = "u_" + Math.random().toString(36).slice(2, 10);
    localStorage.setItem("odyssey-user", id);
  }
  return id;
}

export async function createSession(): Promise<string> {
  const r = await fetch(`${BASE}/api/sessions`, {
    method: "POST",
    headers: { "x-user-id": userId() },
  });
  if (!r.ok) throw new Error("failed to create session");
  const j = await r.json();
  return j.session_id as string;
}

export async function getAgents(): Promise<AgentInfo[]> {
  const r = await fetch(`${BASE}/api/agents`);
  if (!r.ok) return [];
  const j = await r.json();
  return j.agents as AgentInfo[];
}

export async function getSessionState(sessionId: string) {
  const r = await fetch(`${BASE}/api/sessions/${sessionId}/state`, {
    headers: { "x-user-id": userId() },
  });
  if (!r.ok) throw new Error("failed to load session");
  return r.json();
}

/**
 * Stream one turn. The endpoint is a POST returning an SSE body, so we parse the
 * event stream from the fetch reader (EventSource can't POST).
 */
export async function streamChat(
  sessionId: string,
  text: string,
  onEvent: (ev: UIEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const resp = await fetch(`${BASE}/api/chat/${sessionId}/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-user-id": userId() },
    body: JSON.stringify({ text }),
    signal,
  });
  if (!resp.ok || !resp.body) throw new Error(`stream failed: ${resp.status}`);

  await consumeUIEvents(resp, onEvent);
}

/** Resume a graph paused at the approval gate with the user's decision. */
export async function resumeChat(
  sessionId: string,
  decision: { approved: boolean; note?: string; booking_id?: string },
  onEvent: (ev: UIEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const resp = await fetch(`${BASE}/api/chat/${sessionId}/resume`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-user-id": userId() },
    body: JSON.stringify(decision),
    signal,
  });
  if (!resp.ok || !resp.body) throw new Error(`resume failed: ${resp.status}`);
  await consumeUIEvents(resp, onEvent);
}

/** Shared SSE reader for the UIEvent streams (chat + resume). */
async function consumeUIEvents(resp: Response, onEvent: (ev: UIEvent) => void): Promise<void> {
  const reader = resp.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    // Normalize CRLF -> LF: sse-starlette emits \r\n line endings, so frames are
    // separated by \r\n\r\n. Stripping raw \r lets us split on the blank line.
    buffer += decoder.decode(value, { stream: true }).replace(/\r/g, "");
    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      const ev = parseFrame(frame);
      if (ev) onEvent(ev);
    }
  }
}

export async function getNotifications(): Promise<Notification[]> {
  const r = await fetch(`${BASE}/api/notifications`, { headers: { "x-user-id": userId() } });
  if (!r.ok) return [];
  const j = await r.json();
  return j.notifications as Notification[];
}

export async function reorderItinerary(sessionId: string, itinerary: any): Promise<any> {
  const r = await fetch(`${BASE}/api/sessions/${sessionId}/reorder`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-user-id": userId() },
    body: JSON.stringify({ itinerary }),
  });
  if (!r.ok) return null;
  const j = await r.json();
  return j.itinerary;
}

export async function listSessions(): Promise<any[]> {
  const r = await fetch(`${BASE}/api/sessions`, { headers: { "x-user-id": userId() } });
  if (!r.ok) return [];
  return (await r.json()).sessions ?? [];
}

export async function getMemories(): Promise<any[]> {
  const r = await fetch(`${BASE}/api/memory`, { headers: { "x-user-id": userId() } });
  if (!r.ok) return [];
  return (await r.json()).memories ?? [];
}

export async function addMemory(text: string, kind = "preference", tags: string[] = []): Promise<void> {
  await fetch(`${BASE}/api/memory`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-user-id": userId() },
    body: JSON.stringify({ text, kind, tags }),
  }).catch(() => {});
}

export async function deleteMemory(key: string): Promise<void> {
  await fetch(`${BASE}/api/memory/${key}`, {
    method: "DELETE",
    headers: { "x-user-id": userId() },
  }).catch(() => {});
}

export async function recheckConditions(sessionId: string): Promise<{ issues: number }> {
  const r = await fetch(`${BASE}/api/sessions/${sessionId}/recheck`, {
    method: "POST",
    headers: { "x-user-id": userId() },
  });
  if (!r.ok) return { issues: 0 };
  return r.json();
}

export async function markNotificationRead(id: string): Promise<void> {
  await fetch(`${BASE}/api/notifications/${id}/read`, {
    method: "POST",
    headers: { "x-user-id": userId() },
  }).catch(() => {});
}

/** Long-lived subscription to proactive notifications (SSE over fetch reader). */
export async function streamNotifications(
  onNote: (n: Notification) => void,
  signal?: AbortSignal,
): Promise<void> {
  const resp = await fetch(`${BASE}/api/notifications/stream`, {
    headers: { "x-user-id": userId() },
    signal,
  });
  if (!resp.ok || !resp.body) throw new Error("notifications stream failed");
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true }).replace(/\r/g, "");
    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      for (const raw of frame.split("\n")) {
        if (raw.startsWith("data:")) {
          try {
            onNote(JSON.parse(raw.slice(5).trim()) as Notification);
          } catch {
            /* ignore malformed */
          }
        }
      }
    }
  }
}

function parseFrame(frame: string): UIEvent | null {
  let eventType = "message";
  const dataLines: string[] = [];
  for (const raw of frame.split("\n")) {
    const line = raw.trimEnd();
    if (line.startsWith(":")) continue; // comment/heartbeat
    if (line.startsWith("event:")) eventType = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trimStart());
  }
  if (dataLines.length === 0) return null;
  try {
    const parsed = JSON.parse(dataLines.join("\n"));
    return { type: (parsed.type || eventType) as UIEvent["type"], ts: parsed.ts, agent: parsed.agent, data: parsed.data || {} };
  } catch {
    return null;
  }
}
