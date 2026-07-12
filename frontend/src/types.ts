// Shared types mirroring the backend Pydantic schemas (api/schemas.py).

export interface CitizenState {
  id: number;
  lat: number;
  lon: number;
  activity: string;
  traveling: boolean;
  energy: number;
  happiness: number;
}

export interface SimulationMetrics {
  day: number;
  day_name: string;
  time: string;
  population: number;
  traveling: number;
  by_activity: Record<string, number>;
  avg_energy: number;
  avg_happiness: number;
  weather: string;
  temperature_c: number;
  active_events: string[];
}

export interface TickMessage {
  type: "tick";
  metrics: SimulationMetrics;
  citizens: CitizenState[];
}

export interface PoiFeature {
  id: number;
  category: string;
  name: string | null;
  lat: number;
  lon: number;
}

export type WeatherCondition = "clear" | "rain" | "heatwave" | "sandstorm";

export type EventPreset =
  | "riyadh_season"
  | "football_match"
  | "concert"
  | "road_closure"
  | "metro_outage";

export type ControlAction =
  | "play"
  | "pause"
  | "reset"
  | "set_weather"
  | "set_speed"
  | "add_event";

export interface ControlRequest {
  action: ControlAction;
  weather?: WeatherCondition;
  tick_interval_seconds?: number;
  population?: number;
  event?: EventPreset;
}
