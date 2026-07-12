// Thin REST client for the Atlas backend. Paths are relative so the Vite dev
// proxy (and a same-origin production deploy) route them to the API.

import type { ControlRequest, PoiFeature, SimulationMetrics } from "../types";

interface SimulationState {
  running: boolean;
  tick_interval_seconds: number;
  metrics: SimulationMetrics;
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return (await res.json()) as T;
}

export async function fetchPois(): Promise<PoiFeature[]> {
  return json(await fetch("/api/city/pois"));
}

export async function fetchState(): Promise<SimulationState> {
  return json(await fetch("/api/simulation/state"));
}

export async function sendControl(request: ControlRequest): Promise<SimulationState> {
  return json(
    await fetch("/api/simulation/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    }),
  );
}
