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

  const statusColor =
    status === "open" ? "bg-emerald-500" : status === "connecting" ? "bg-amber-500" : "bg-rose-500";

  return (
    <div className="relative h-full w-full overflow-hidden">
      <MapView citizens={tick?.citizens ?? []} pois={pois} showPois={showPois} />

      {/* Header */}
      <div className="pointer-events-none absolute left-4 top-4 z-10 flex items-center gap-2">
        <div className="pointer-events-auto rounded-xl bg-slate-900/80 px-4 py-2 shadow-xl backdrop-blur">
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold tracking-tight text-slate-50">Atlas</span>
            <span className="text-xs text-slate-400">Riyadh Digital Twin</span>
            <span className={`ml-1 inline-block h-2 w-2 rounded-full ${statusColor}`} />
          </div>
        </div>
      </div>

      {/* Left control panel */}
      <div className="absolute left-4 top-20 z-10">
        <ControlPanel showPois={showPois} onTogglePois={setShowPois} />
      </div>

      {/* Right metrics panel */}
      <div className="absolute right-4 top-4 z-10">
        <MetricsPanel metrics={tick?.metrics ?? null} connected={status === "open"} />
      </div>
    </div>
  );
}
