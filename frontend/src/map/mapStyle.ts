import type { StyleSpecification } from "maplibre-gl";

// A self-contained dark raster basemap using CARTO's free tiles — no API key
// required, which keeps local development friction-free.
export const DARK_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    carto: {
      type: "raster",
      tiles: [
        "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
        "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
        "https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
      ],
      tileSize: 256,
      attribution:
        '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> · © <a href="https://carto.com/attributions">CARTO</a>',
    },
  },
  layers: [
    { id: "background", type: "background", paint: { "background-color": "#0b0f19" } },
    { id: "carto", type: "raster", source: "carto" },
  ],
};

export const RIYADH_CENTER: [number, number] = [46.6753, 24.7136];
