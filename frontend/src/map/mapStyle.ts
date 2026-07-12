import type { StyleSpecification } from "maplibre-gl";

// A clean, light basemap using CARTO's free Positron tiles — minimal greys and
// whites so the coloured citizen dots read clearly. No API key required.
export const LIGHT_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    carto: {
      type: "raster",
      tiles: [
        "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        "https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
      ],
      tileSize: 256,
      attribution:
        '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> · © <a href="https://carto.com/attributions">CARTO</a>',
    },
  },
  layers: [
    { id: "background", type: "background", paint: { "background-color": "#f8fafc" } },
    { id: "carto", type: "raster", source: "carto" },
  ],
};

export const RIYADH_CENTER: [number, number] = [46.6753, 24.7136];
