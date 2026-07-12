import maplibregl from "maplibre-gl";
import { useEffect, useRef } from "react";

import type { CitizenState, PoiFeature } from "../types";
import { ACTIVITY_COLORS, POI_COLORS, colorMatch, toGeoJSON } from "../theme";
import { DARK_STYLE, RIYADH_CENTER } from "./mapStyle";

interface Props {
  citizens: CitizenState[];
  pois: PoiFeature[];
  showPois: boolean;
}

const EMPTY_FC = { type: "FeatureCollection" as const, features: [] };

function citizensToGeoJSON(citizens: CitizenState[]) {
  return {
    type: "FeatureCollection" as const,
    features: citizens.map((c) => ({
      type: "Feature" as const,
      properties: { activity: c.activity, traveling: c.traveling },
      geometry: { type: "Point" as const, coordinates: [c.lon, c.lat] },
    })),
  };
}

export default function MapView({ citizens, pois, showPois }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const readyRef = useRef(false);

  // Initialise the map once.
  useEffect(() => {
    if (!containerRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: DARK_STYLE,
      center: RIYADH_CENTER,
      zoom: 11,
      attributionControl: { compact: true },
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");

    map.on("load", () => {
      map.addSource("pois", { type: "geojson", data: EMPTY_FC });
      map.addLayer({
        id: "pois",
        type: "circle",
        source: "pois",
        paint: {
          "circle-radius": 4,
          "circle-color": colorMatch("category", POI_COLORS, "#94a3b8") as never,
          "circle-opacity": 0.9,
          "circle-stroke-width": 1,
          "circle-stroke-color": "#0b0f19",
        },
      });

      map.addSource("citizens", { type: "geojson", data: EMPTY_FC });
      map.addLayer({
        id: "citizens",
        type: "circle",
        source: "citizens",
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 9, 2, 14, 5] as never,
          "circle-color": colorMatch("activity", ACTIVITY_COLORS, "#e2e8f0") as never,
          "circle-opacity": 0.85,
          "circle-stroke-width": ["case", ["get", "traveling"], 1, 0] as never,
          "circle-stroke-color": "#f8fafc",
        },
      });
      readyRef.current = true;
    });

    return () => {
      map.remove();
      mapRef.current = null;
      readyRef.current = false;
    };
  }, []);

  // Push citizen updates on every tick.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !readyRef.current) return;
    const source = map.getSource("citizens") as maplibregl.GeoJSONSource | undefined;
    source?.setData(citizensToGeoJSON(citizens));
  }, [citizens]);

  // Update the POI layer when data or visibility changes.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !readyRef.current) return;
    const source = map.getSource("pois") as maplibregl.GeoJSONSource | undefined;
    source?.setData(showPois ? toGeoJSON(pois) : EMPTY_FC);
  }, [pois, showPois]);

  return <div ref={containerRef} className="absolute inset-0" />;
}
