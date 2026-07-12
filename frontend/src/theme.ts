// Colour palette shared by the map layers and the UI legend/panels.

import type { PoiFeature } from "./types";

// One colour per citizen activity — used for the moving-agent dots.
export const ACTIVITY_COLORS: Record<string, string> = {
  sleep: "#475569",
  home: "#64748b",
  work: "#3b82f6",
  pray: "#22c55e",
  eat: "#f59e0b",
  shop: "#a855f7",
  exercise: "#ef4444",
  socialize: "#ec4899",
};

export const ACTIVITY_LABELS: Record<string, string> = {
  sleep: "Sleeping",
  home: "At home",
  work: "Working",
  pray: "Praying",
  eat: "Eating",
  shop: "Shopping",
  exercise: "Exercising",
  socialize: "Socialising",
};

// Colours for the static POI reference layer.
export const POI_COLORS: Record<string, string> = {
  mosque: "#34d399",
  mall: "#c084fc",
  park: "#4ade80",
  hospital: "#f87171",
  metro_station: "#38bdf8",
  university: "#fbbf24",
};

export const POI_LABELS: Record<string, string> = {
  mosque: "Mosques",
  mall: "Malls",
  park: "Parks",
  hospital: "Hospitals",
  metro_station: "Metro",
  university: "Universities",
};

export const WEATHER_ICONS: Record<string, string> = {
  clear: "☀️",
  rain: "🌧️",
  heatwave: "🔥",
  sandstorm: "🌪️",
};

// Build a match expression for MapLibre from a colour map.
export function colorMatch(
  property: string,
  colors: Record<string, string>,
  fallback: string,
): unknown[] {
  const expr: unknown[] = ["match", ["get", property]];
  for (const [key, color] of Object.entries(colors)) {
    expr.push(key, color);
  }
  expr.push(fallback);
  return expr;
}

export function toGeoJSON(features: PoiFeature[]) {
  return {
    type: "FeatureCollection" as const,
    features: features.map((f) => ({
      type: "Feature" as const,
      properties: { category: f.category, name: f.name ?? "" },
      geometry: { type: "Point" as const, coordinates: [f.lon, f.lat] },
    })),
  };
}
