"use client";

import { useEffect, useRef } from "react";
import maplibregl, { type Map as MLMap, Marker, LngLatBounds } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useStore } from "@/lib/store";
import type { ItineraryItem } from "@/lib/types";
import { MapPinned } from "lucide-react";

const STYLE_URL =
  process.env.NEXT_PUBLIC_MAP_STYLE_URL || "https://tiles.openfreemap.org/styles/liberty";

// Day palette (indexed by day-1). Matches the timeline's day accents.
export const DAY_COLORS = [
  "#6366f1", "#14b8a6", "#f59e0b", "#0ea5e9", "#a855f7",
  "#10b981", "#ef4444", "#ec4899", "#84cc16", "#f97316",
];

interface Placed extends ItineraryItem {
  day: number;
  index: number;
}

function placedItems(itinerary: ReturnType<typeof useStore.getState>["itinerary"]): Placed[] {
  if (!itinerary) return [];
  const out: Placed[] = [];
  for (const d of itinerary.days) {
    let idx = 0;
    for (const item of d.items) {
      if (item.geo && typeof item.geo.lat === "number") {
        idx++;
        out.push({ ...item, day: d.day, index: idx });
      }
    }
  }
  return out;
}

function markerEl(p: Placed, selected: boolean): HTMLDivElement {
  const color = DAY_COLORS[(p.day - 1) % DAY_COLORS.length];
  const el = document.createElement("div");
  el.className = "odyssey-marker";
  el.style.cssText = `
    width:${selected ? 30 : 24}px;height:${selected ? 30 : 24}px;border-radius:50% 50% 50% 0;
    transform:rotate(-45deg);background:${color};display:grid;place-items:center;cursor:pointer;
    box-shadow:0 2px 8px rgba(0,0,0,.35);border:2px solid rgba(255,255,255,.9);
    transition:width .15s,height .15s;${selected ? "z-index:10;" : ""}`;
  const label = document.createElement("span");
  label.textContent = String(p.index);
  label.style.cssText = `transform:rotate(45deg);color:#fff;font-size:11px;font-weight:700;font-family:var(--font-sans)`;
  el.appendChild(label);
  return el;
}

export function MapCanvas() {
  const mapRef = useRef<MLMap | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const markersRef = useRef<Map<string, Marker>>(new Map());
  const itinerary = useStore((s) => s.itinerary);
  const selectedItemId = useStore((s) => s.selectedItemId);
  const selectItem = useStore((s) => s.selectItem);

  // init
  useEffect(() => {
    if (mapRef.current || !containerRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: STYLE_URL,
      center: [10, 30],
      zoom: 1.4,
      attributionControl: { compact: true },
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // sync markers with itinerary
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const apply = () => {
      markersRef.current.forEach((m) => m.remove());
      markersRef.current.clear();

      const items = placedItems(itinerary);
      if (items.length === 0) {
        if (itinerary?.center) map.flyTo({ center: [itinerary.center.lng, itinerary.center.lat], zoom: 11 });
        return;
      }
      const bounds = new LngLatBounds();
      for (const p of items) {
        const el = markerEl(p, p.id === selectedItemId);
        el.addEventListener("click", () => selectItem(p.id));
        const marker = new Marker({ element: el, anchor: "bottom" })
          .setLngLat([p.geo!.lng, p.geo!.lat])
          .setPopup(
            new maplibregl.Popup({ offset: 18, closeButton: false }).setHTML(
              `<div style="font-weight:600;font-size:12px;margin-bottom:2px">Day ${p.day} - ${escapeHtml(p.title)}</div>` +
                (p.start ? `<div style="font-size:11px;opacity:.7">${escapeHtml(p.start)}${p.end ? " - " + escapeHtml(p.end) : ""}</div>` : ""),
            ),
          )
          .addTo(map);
        markersRef.current.set(p.id, marker);
        bounds.extend([p.geo!.lng, p.geo!.lat]);
      }
      try {
        map.fitBounds(bounds, { padding: 70, maxZoom: 14, duration: 700 });
      } catch {
        /* single point */
      }
    };
    if (map.isStyleLoaded()) apply();
    else map.once("load", apply);
  }, [itinerary, selectItem]); // eslint-disable-line react-hooks/exhaustive-deps

  // react to selection: refresh marker sizes + fly
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const items = placedItems(itinerary);
    for (const p of items) {
      const marker = markersRef.current.get(p.id);
      if (!marker) continue;
      const el = marker.getElement();
      const selected = p.id === selectedItemId;
      el.style.width = selected ? "30px" : "24px";
      el.style.height = selected ? "30px" : "24px";
      el.style.zIndex = selected ? "10" : "";
    }
    if (selectedItemId) {
      const sel = items.find((p) => p.id === selectedItemId);
      if (sel?.geo) map.flyTo({ center: [sel.geo.lng, sel.geo.lat], zoom: 14, duration: 600 });
    }
  }, [selectedItemId, itinerary]);

  const hasPlan = !!itinerary && placedItems(itinerary).length > 0;

  return (
    <div className="relative h-full w-full">
      <div ref={containerRef} className="h-full w-full" />
      {!hasPlan && (
        <div className="pointer-events-none absolute inset-0 grid place-items-center">
          <div className="flex flex-col items-center gap-2 rounded-xl border border-border bg-surface/80 px-5 py-4 text-center backdrop-blur">
            <MapPinned className="h-5 w-5 text-faint" />
            <p className="max-w-[200px] text-xs text-muted">
              Your itinerary map appears here as the agents place real spots.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

function escapeHtml(s: string) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);
}
