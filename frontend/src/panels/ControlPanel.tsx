import { useState } from "react";

import { sendControl } from "../api/client";
import type { EventPreset, WeatherCondition } from "../types";
import { POI_COLORS, POI_LABELS, WEATHER_ICONS } from "../theme";

interface Props {
  showPois: boolean;
  onTogglePois: (value: boolean) => void;
}

const WEATHERS: WeatherCondition[] = ["clear", "rain", "heatwave", "sandstorm"];
const EVENTS: { id: EventPreset; label: string }[] = [
  { id: "riyadh_season", label: "Riyadh Season" },
  { id: "football_match", label: "Football Match" },
  { id: "concert", label: "Concert" },
  { id: "road_closure", label: "Road Closure" },
  { id: "metro_outage", label: "Metro Outage" },
];

export default function ControlPanel({ showPois, onTogglePois }: Props) {
  const [running, setRunning] = useState(true);
  const [weather, setWeather] = useState<WeatherCondition>("clear");
  const [speed, setSpeed] = useState(1);

  const togglePlay = async () => {
    const next = !running;
    setRunning(next);
    await sendControl({ action: next ? "play" : "pause" });
  };

  const changeWeather = async (w: WeatherCondition) => {
    setWeather(w);
    await sendControl({ action: "set_weather", weather: w });
  };

  const changeSpeed = async (value: number) => {
    setSpeed(value);
    // Higher slider value == faster == shorter interval between ticks.
    await sendControl({ action: "set_speed", tick_interval_seconds: 1 / value });
  };

  return (
    <div className="w-72 space-y-4 rounded-xl bg-slate-900/80 p-4 shadow-xl backdrop-blur">
      <div className="flex items-center gap-2">
        <button
          onClick={togglePlay}
          className="flex-1 rounded-lg bg-sky-600 px-3 py-2 text-sm font-semibold text-white hover:bg-sky-500"
        >
          {running ? "⏸ Pause" : "▶ Play"}
        </button>
        <button
          onClick={() => sendControl({ action: "reset" })}
          className="rounded-lg bg-slate-700 px-3 py-2 text-sm font-semibold text-slate-100 hover:bg-slate-600"
        >
          ↺ Reset
        </button>
      </div>

      <div>
        <div className="mb-1 text-[10px] uppercase tracking-wide text-slate-400">
          Speed · {speed}×
        </div>
        <input
          type="range"
          min={0.5}
          max={5}
          step={0.5}
          value={speed}
          onChange={(e) => changeSpeed(Number(e.target.value))}
          className="w-full accent-sky-500"
        />
      </div>

      <div>
        <div className="mb-1 text-[10px] uppercase tracking-wide text-slate-400">Weather</div>
        <div className="grid grid-cols-4 gap-1">
          {WEATHERS.map((w) => (
            <button
              key={w}
              onClick={() => changeWeather(w)}
              title={w}
              className={`rounded-lg py-2 text-lg ${
                weather === w ? "bg-sky-600" : "bg-slate-800 hover:bg-slate-700"
              }`}
            >
              {WEATHER_ICONS[w]}
            </button>
          ))}
        </div>
      </div>

      <div>
        <div className="mb-1 text-[10px] uppercase tracking-wide text-slate-400">
          Trigger event
        </div>
        <div className="grid grid-cols-1 gap-1">
          {EVENTS.map((e) => (
            <button
              key={e.id}
              onClick={() => sendControl({ action: "add_event", event: e.id })}
              className="rounded-lg bg-slate-800 px-3 py-1.5 text-left text-xs text-slate-200 hover:bg-slate-700"
            >
              {e.label}
            </button>
          ))}
        </div>
      </div>

      <label className="flex items-center gap-2 text-xs text-slate-300">
        <input
          type="checkbox"
          checked={showPois}
          onChange={(e) => onTogglePois(e.target.checked)}
          className="accent-sky-500"
        />
        Show landmarks
      </label>
      {showPois && (
        <div className="grid grid-cols-2 gap-1 text-[11px] text-slate-400">
          {Object.keys(POI_COLORS).map((cat) => (
            <div key={cat} className="flex items-center gap-1.5">
              <span
                className="inline-block h-2 w-2 rounded-full"
                style={{ background: POI_COLORS[cat] }}
              />
              {POI_LABELS[cat] ?? cat}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
