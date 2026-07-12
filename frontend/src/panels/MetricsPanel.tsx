import type { SimulationMetrics } from "../types";
import { ACTIVITY_COLORS, ACTIVITY_LABELS, WEATHER_ICONS } from "../theme";

interface Props {
  metrics: SimulationMetrics | null;
  connected: boolean;
}

const CARD =
  "rounded-2xl border border-slate-200/70 bg-white/85 shadow-lg shadow-slate-900/5 backdrop-blur-md";

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl bg-slate-50 px-3 py-2 ring-1 ring-slate-100">
      <div className="text-[10px] font-medium uppercase tracking-wide text-slate-400">{label}</div>
      <div className="text-lg font-bold text-slate-900">{value}</div>
    </div>
  );
}

export default function MetricsPanel({ metrics, connected }: Props) {
  if (!metrics) {
    return (
      <div className={`${CARD} w-72 p-4 text-sm text-slate-500`}>
        {connected ? "Waiting for first tick…" : "Connecting to simulation…"}
      </div>
    );
  }

  const total = metrics.population || 1;
  const sorted = Object.entries(metrics.by_activity).sort((a, b) => b[1] - a[1]);

  return (
    <div className={`${CARD} w-72 p-4`}>
      <div className="mb-3 flex items-center justify-between">
        <div>
          <div className="text-xs font-medium text-slate-400">{metrics.day_name}</div>
          <div className="text-3xl font-bold tracking-tight text-slate-900">{metrics.time}</div>
        </div>
        <div className="text-right">
          <div className="text-3xl leading-none">{WEATHER_ICONS[metrics.weather] ?? "🌡️"}</div>
          <div className="mt-1 text-xs capitalize text-slate-500">
            {metrics.weather} · {metrics.temperature_c}°C
          </div>
        </div>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-2">
        <Stat label="Population" value={metrics.population.toLocaleString()} />
        <Stat label="Traveling" value={metrics.traveling} />
        <Stat label="Avg energy" value={metrics.avg_energy} />
        <Stat label="Avg happiness" value={metrics.avg_happiness} />
      </div>

      <div className="mb-2 text-[10px] font-medium uppercase tracking-wide text-slate-400">
        Activity right now
      </div>
      <div className="space-y-1.5">
        {sorted.map(([activity, count]) => (
          <div key={activity} className="flex items-center gap-2 text-xs">
            <span
              className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
              style={{ background: ACTIVITY_COLORS[activity] ?? "#64748b" }}
            />
            <span className="w-20 text-slate-600">{ACTIVITY_LABELS[activity] ?? activity}</span>
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${(count / total) * 100}%`,
                  background: ACTIVITY_COLORS[activity] ?? "#64748b",
                }}
              />
            </div>
            <span className="w-9 text-right font-medium tabular-nums text-slate-500">{count}</span>
          </div>
        ))}
      </div>

      {metrics.active_events.length > 0 && (
        <div className="mt-3 rounded-xl bg-amber-50 p-2.5 text-xs font-medium text-amber-700 ring-1 ring-amber-200">
          🎉 {[...new Set(metrics.active_events)].join(" · ")}
        </div>
      )}
    </div>
  );
}
