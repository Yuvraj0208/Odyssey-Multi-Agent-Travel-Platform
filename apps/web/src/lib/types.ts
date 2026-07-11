// UI event + domain types. Mirror of the backend contracts in
// apps/api/odyssey/schemas/events.py and schemas/trip.py.

export type UIEventType =
  | "session_start"
  | "agent_enter"
  | "agent_exit"
  | "token"
  | "message"
  | "tool_start"
  | "tool_end"
  | "handoff"
  | "plan_updated"
  | "options"
  | "approval_required"
  | "booking_updated"
  | "telemetry"
  | "error"
  | "done";

export interface UIEvent {
  type: UIEventType;
  ts: number;
  agent?: string | null;
  data: Record<string, any>;
}

export interface AgentInfo {
  name: string;
  description: string;
  phase: number;
  role?: "supervisor" | "specialist";
}

export type AgentStatus = "idle" | "active" | "done" | "error";

export interface Geo {
  lat: number;
  lng: number;
  name?: string | null;
}

export interface ItineraryItem {
  id: string;
  type: string;
  title: string;
  description?: string | null;
  geo?: Geo | null;
  start?: string | null;
  end?: string | null;
  duration_min?: number | null;
  cost_estimate?: number | null;
  currency?: string;
  source?: string | null;
  booking_ref?: string | null;
  weather_note?: string | null;
  tags?: string[];
  transit_to_next_min?: number | null;
  transit_to_next_km?: number | null;
  transit_mode?: string | null;
}

export interface ItineraryDay {
  day: number;
  date?: string | null;
  summary?: string | null;
  items: ItineraryItem[];
  travel_min?: number | null;
  feasible?: boolean | null;
}

export interface Itinerary {
  destination?: string | null;
  center?: Geo | null;
  days: ItineraryDay[];
  currency?: string;
  summary?: string | null;
  updated_at?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  agent?: string | null;
  text: string;
  streaming?: boolean;
}

export interface ToolActivity {
  id: string;
  agent: string;
  tool: string;
  argsPreview?: string;
  summary?: string;
  ok?: boolean;
  durationMs?: number;
  running: boolean;
  ts: number;
}

export interface HandoffActivity {
  id: string;
  from: string;
  to: string;
  reason: string;
  ts: number;
}

export interface Offer {
  id: string;
  type: string;
  provider: string;
  title: string;
  price: number;
  currency?: string;
  details?: Record<string, any>;
  geo?: Geo | null;
  cancellation?: string;
}

export interface Booking {
  id: string;
  type: string;
  action?: string;
  provider: string;
  title: string;
  price: number;
  currency?: string;
  status: string;
  booking_ref?: string | null;
  cancellation?: string;
  details?: Record<string, any>;
}

export interface ApprovalPayload {
  kind: string;
  bookings: Booking[];
  total: number;
  currency: string;
}

export type OptionsMap = { flights?: Offer[]; hotels?: Offer[]; activities?: Offer[] };

export interface Notification {
  id: string;
  kind: "weather" | "price" | "availability" | "info";
  severity: "info" | "warning";
  title: string;
  body: string;
  session_id?: string | null;
  suggested_prompt?: string | null;
  created_at: number;
  read?: boolean;
}

export interface Telemetry {
  session_id: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  model: string;
  tool_calls: number;
  agent_steps: number;
  last_latency_ms: number;
}
