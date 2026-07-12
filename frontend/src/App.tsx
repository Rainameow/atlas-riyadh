import { useEffect, useState } from "react";

import { fetchPois } from "./api/client";
import { useSimulationSocket } from "./hooks/useSimulationSocket";
import MapView from "./map/MapView";
import ControlPanel from "./panels/ControlPanel";
import MetricsPanel from "./panels/MetricsPanel";
import type { PoiFeature } from "./types";

export default function App() {
  const { tick, status } = useSimulationSocket();
  const [pois, setPois] = useState<PoiFeature[]>([]);
  const [showPois, setShowPois] = useState(true);

  useEffect(() => {
    fetchPois()
      .then(setPois)
      .catch(() => setPois([]));
  }, []);

  const statusLabel =
    status === "open" ? "Live" : status === "connecting" ? "Connecting" : "Offline";
  const statusColor =
    status === "open" ? "bg-emerald-500" : status === "connecting" ? "bg-amber-500" : "bg-rose-500";

  return (
    <div className="relative h-full w-full overflow-hidden">
      <MapView citizens={tick?.citizens ?? []} pois={pois} showPois={showPois} />

      {/* Brand header */}
      <div className="absolute left-5 top-5 z-10">
        <div className="flex items-center gap-3 rounded-2xl border border-slate-200/70 bg-white/85 px-4 py-2.5 shadow-lg shadow-slate-900/5 backdrop-blur-md">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-sky-500 to-indigo-600 text-lg font-black text-white shadow-sm">
            A
          </div>
          <div className="leading-tight">
            <div className="text-base font-bold tracking-tight text-slate-900">Atlas</div>
            <div className="text-[11px] text-slate-500">Riyadh · Digital Twin</div>
          </div>
          <div className="ml-2 flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1">
            <span className={`inline-block h-2 w-2 rounded-full ${statusColor}`} />
            <span className="text-[11px] font-medium text-slate-600">{statusLabel}</span>
          </div>
        </div>
      </div>

      {/* Left control panel */}
      <div className="absolute left-5 top-24 z-10">
        <ControlPanel showPois={showPois} onTogglePois={setShowPois} />
      </div>

      {/* Right metrics panel */}
      <div className="absolute right-5 top-5 z-10">
        <MetricsPanel metrics={tick?.metrics ?? null} connected={status === "open"} />
      </div>
    </div>
  );
}
