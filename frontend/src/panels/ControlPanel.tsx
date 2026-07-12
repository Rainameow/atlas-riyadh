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

const SECTION = "text-[10px] font-medium uppercase tracking-wide text-slate-400";

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
    await sendControl({ action: "set_speed", tick_interval_seconds: 1 / value });
  };

  return (
    <div className="w-72 space-y-4 rounded-2xl border border-slate-200/70 bg-white/85 p-4 shadow-lg shadow-slate-900/5 backdrop-blur-md">
      <div className="flex items-center gap-2">
        <button
          onClick={togglePlay}
          className="flex-1 rounded-xl bg-gradient-to-br from-sky-500 to-indigo-600 px-3 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:brightness-110"
        >
          {running ? "⏸  Pause" : "▶  Play"}
        </button>
        <button
          onClick={() => sendControl({ action: "reset" })}
          className="rounded-xl bg-slate-100 px-3 py-2.5 text-sm font-semibold text-slate-700 ring-1 ring-slate-200 transition hover:bg-slate-200"
        >
          ↺
        </button>
      </div>

      <div>
        <div className={`mb-1.5 ${SECTION}`}>Speed · {speed}×</div>
        <input
          type="range"
          min={0.5}
          max={5}
          step={0.5}
          value={speed}
          onChange={(e) => changeSpeed(Number(e.target.value))}
          className="w-full accent-sky-600"
        />
      </div>

      <div>
        <div className={`mb-1.5 ${SECTION}`}>Weather</div>
        <div className="grid grid-cols-4 gap-1.5">
          {WEATHERS.map((w) => (
            <button
              key={w}
              onClick={() => changeWeather(w)}
              title={w}
              className={`rounded-xl py-2 text-lg transition ${
                weather === w
                  ? "bg-sky-100 ring-2 ring-sky-500"
                  : "bg-slate-50 ring-1 ring-slate-200 hover:bg-slate-100"
              }`}
            >
              {WEATHER_ICONS[w]}
            </button>
          ))}
        </div>
      </div>

      <div>
        <div className={`mb-1.5 ${SECTION}`}>Trigger event</div>
        <div className="grid grid-cols-1 gap-1.5">
          {EVENTS.map((e) => (
            <button
              key={e.id}
              onClick={() => sendControl({ action: "add_event", event: e.id })}
              className="rounded-xl bg-slate-50 px-3 py-2 text-left text-xs font-medium text-slate-700 ring-1 ring-slate-200 transition hover:bg-slate-100"
            >
              {e.label}
            </button>
          ))}
        </div>
      </div>

      <div className="border-t border-slate-100 pt-3">
        <label className="flex cursor-pointer items-center gap-2 text-xs font-medium text-slate-600">
          <input
            type="checkbox"
            checked={showPois}
            onChange={(e) => onTogglePois(e.target.checked)}
            className="accent-sky-600"
          />
          Show landmarks
        </label>
        {showPois && (
          <div className="mt-2 grid grid-cols-2 gap-1.5 text-[11px] text-slate-500">
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
    </div>
  );
}
