import maplibregl from "maplibre-gl";
import { useEffect, useRef } from "react";

import type { CitizenState, PoiFeature } from "../types";
import { ACTIVITY_COLORS, POI_COLORS, colorMatch, toGeoJSON } from "../theme";
import { LIGHT_STYLE, RIYADH_CENTER } from "./mapStyle";

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
      properties: { activity: c.activity, traveling: c.traveling ? 1 : 0 },
      geometry: { type: "Point" as const, coordinates: [c.lon, c.lat] },
    })),
  };
}

export default function MapView({ citizens, pois, showPois }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const readyRef = useRef(false);

  useEffect(() => {
    if (!containerRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: LIGHT_STYLE,
      center: RIYADH_CENTER,
      zoom: 11,
      minZoom: 9,
      maxZoom: 16,
      attributionControl: { compact: true },
      fadeDuration: 150,
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");

    map.on("load", () => {
      // A subtle blue city-light wash under the basemap darkens the edges.
      map.addSource("pois", { type: "geojson", data: EMPTY_FC });
      map.addLayer({
        id: "pois-glow",
        type: "circle",
        source: "pois",
        paint: {
          "circle-radius": 9,
          "circle-color": colorMatch("category", POI_COLORS, "#94a3b8") as never,
          "circle-blur": 1,
          "circle-opacity": 0.35,
        },
      });
      map.addLayer({
        id: "pois",
        type: "circle",
        source: "pois",
        paint: {
          "circle-radius": 3.5,
          "circle-color": colorMatch("category", POI_COLORS, "#94a3b8") as never,
          "circle-opacity": 0.95,
          "circle-stroke-width": 1.2,
          "circle-stroke-color": "rgba(255,255,255,0.9)",
        },
      });

      // Citizens: a soft coloured halo beneath a crisp core, with a subtle dark
      // ring so the dots stay defined against the light basemap.
      map.addSource("citizens", { type: "geojson", data: EMPTY_FC });
      map.addLayer({
        id: "citizens-glow",
        type: "circle",
        source: "citizens",
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 9, 3.5, 14, 9] as never,
          "circle-color": colorMatch("activity", ACTIVITY_COLORS, "#64748b") as never,
          "circle-blur": 0.9,
          "circle-opacity": 0.3,
        },
      });
      map.addLayer({
        id: "citizens",
        type: "circle",
        source: "citizens",
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 9, 2.4, 14, 5.5] as never,
          "circle-color": colorMatch("activity", ACTIVITY_COLORS, "#64748b") as never,
          "circle-opacity": 0.95,
          "circle-stroke-width": ["case", ["==", ["get", "traveling"], 1], 1.4, 0.6] as never,
          "circle-stroke-color": "rgba(255,255,255,0.9)",
        },
      });

      readyRef.current = true;
      map.resize();
    });

    return () => {
      map.remove();
      mapRef.current = null;
      readyRef.current = false;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !readyRef.current) return;
    const source = map.getSource("citizens") as maplibregl.GeoJSONSource | undefined;
    source?.setData(citizensToGeoJSON(citizens));
  }, [citizens]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !readyRef.current) return;
    const source = map.getSource("pois") as maplibregl.GeoJSONSource | undefined;
    source?.setData(showPois ? toGeoJSON(pois) : EMPTY_FC);
  }, [pois, showPois]);

  // Inline styles win over MapLibre's unlayered `.maplibregl-map` rule, which
  // otherwise overrides Tailwind's layered utilities and collapses the height.
  return (
    <div
      ref={containerRef}
      style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
    />
  );
}
