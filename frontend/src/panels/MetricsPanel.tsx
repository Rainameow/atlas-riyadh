import type { SimulationMetrics } from "../types";
import { ACTIVITY_COLORS, ACTIVITY_LABELS, WEATHER_ICONS } from "../theme";

interface Props {
  metrics: SimulationMetrics | null;
  connected: boolean;
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg bg-slate-800/60 px-3 py-2">
      <div className="text-[10px] uppercase tracking-wide text-slate-400">{label}</div>
      <div className="text-lg font-semibold text-slate-100">{value}</div>
    </div>
  );
}

export default function MetricsPanel({ metrics, connected }: Props) {
  if (!metrics) {
    return (
      <div className="rounded-xl bg-slate-900/80 p-4 text-sm text-slate-400 backdrop-blur">
        {connected ? "Waiting for first tick…" : "Connecting to simulation…"}
      </div>
    );
  }

  const total = metrics.population || 1;
  const sorted = Object.entries(metrics.by_activity).sort((a, b) => b[1] - a[1]);

  return (
    <div className="w-72 rounded-xl bg-slate-900/80 p-4 shadow-xl backdrop-blur">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <div className="text-xs text-slate-400">{metrics.day_name}</div>
          <div className="text-2xl font-bold text-slate-50">{metrics.time}</div>
        </div>
        <div className="text-right">
          <div className="text-2xl">{WEATHER_ICONS[metrics.weather] ?? "🌡️"}</div>
          <div className="text-xs capitalize text-slate-300">
            {metrics.weather} · {metrics.temperature_c}°C
          </div>
        </div>
      </div>

      <div className="mb-3 grid grid-cols-2 gap-2">
        <Stat label="Population" value={metrics.population} />
        <Stat label="Traveling" value={metrics.traveling} />
        <Stat label="Avg energy" value={metrics.avg_energy} />
        <Stat label="Avg happiness" value={metrics.avg_happiness} />
      </div>

      <div className="mb-1 text-[10px] uppercase tracking-wide text-slate-400">Activity</div>
      <div className="space-y-1">
        {sorted.map(([activity, count]) => (
          <div key={activity} className="flex items-center gap-2 text-xs">
            <span
              className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
              style={{ background: ACTIVITY_COLORS[activity] ?? "#e2e8f0" }}
            />
            <span className="w-20 text-slate-300">
              {ACTIVITY_LABELS[activity] ?? activity}
            </span>
            <div className="h-1.5 flex-1 overflow-hidden rounded bg-slate-800">
              <div
                className="h-full rounded"
                style={{
                  width: `${(count / total) * 100}%`,
                  background: ACTIVITY_COLORS[activity] ?? "#e2e8f0",
                }}
              />
            </div>
            <span className="w-8 text-right tabular-nums text-slate-400">{count}</span>
          </div>
        ))}
      </div>

      {metrics.active_events.length > 0 && (
        <div className="mt-3 rounded-lg bg-amber-500/10 p-2 text-xs text-amber-300">
          🎉 {metrics.active_events.join(", ")}
        </div>
      )}
    </div>
  );
}
