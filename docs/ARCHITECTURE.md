# Atlas — Architecture

Atlas is an agent-based digital twin platform that simulates real cities. The
first supported city is Riyadh, Saudi Arabia. This document describes the
system design, the layer boundaries, and the mapping from the requested project
structure to the implemented monorepo.

The simulation is driven by deterministic, rule-based autonomous agents (a
behaviour state machine over real geospatial data), not machine learning or an
LLM. The layered design keeps the engine independent so learned decision models
could be introduced later without touching the API, persistence, or transport.

## Layered design

```
Frontend (React/TS/Vite/MapLibre)
        │  REST + WebSocket
API layer (FastAPI)
        │
Simulation engine (pure Python)  ◄──►  Persistence (PostGIS + Redis)
        │
City data layer (OSMnx/GeoPandas/NetworkX/Shapely)
```

**The dependency rule.** `atlas_core` (the simulation engine and city data
layer) has **no dependency** on FastAPI, SQLAlchemy, or Redis. Outer layers
depend on the core; the core never imports outward. This keeps the engine
unit-testable in isolation and lets the transport/persistence layers be swapped
without touching simulation logic.

## Folder structure

The brief requested these top-level areas: `backend`, `frontend`, `simulation`,
`api`, `database`, `docs`, `tests`. They map onto the monorepo as follows so the
Python package stays cohesive and importable:

| Requested | Implemented location | Notes |
|-----------|---------------------|-------|
| backend | `backend/` | Python workspace root (`pyproject.toml`) |
| simulation | `backend/atlas_core/simulation/` | The pure engine |
| api | `backend/api/` | FastAPI app, routers, WebSocket |
| database | `backend/database/` | PostGIS init SQL, Alembic migrations |
| tests | `backend/tests/` | `unit/` + `integration/` |
| docs | `docs/` | This document and runbooks |
| frontend | `frontend/` | React app (Milestone 5) |

```
backend/
├── atlas_core/
│   ├── config/         # pydantic-settings config + structlog logging
│   ├── city/           # OSM ingest, road graph, POIs, spatial index (M1)
│   ├── simulation/     # agents, routing, schedule FSM, weather, events (M2)
│   ├── persistence/    # SQLAlchemy models, repositories, Redis (M3)
│   └── schemas/        # Pydantic DTOs shared with the API
├── api/                # FastAPI app (M4)
├── database/init/      # PostGIS extension bootstrap SQL
├── tests/
└── pyproject.toml
```

## Configuration

All configuration flows through `atlas_core.config.get_settings()`, a cached
`pydantic-settings` singleton. Environment variables use the `ATLAS_` prefix
with per-group sub-prefixes (`ATLAS_CITY_`, `ATLAS_DB_`, `ATLAS_REDIS_`,
`ATLAS_SIM_`). See `.env.example`. There are no scattered `os.getenv` calls.

## Movement correctness

A core requirement: **citizens must not move in straight lines.** Each citizen
holds a route of real OSM graph nodes computed with `networkx.shortest_path`
(weighted by edge length / travel time). Screen position is interpolated *along
the real edge geometries* using cumulative distance, so agents follow the actual
road network. This is implemented in `atlas_core.simulation.routing` (M2) on top
of the road graph built in M1.

## Milestone roadmap

- **M0 — Foundation** *(complete)*: monorepo layout, tooling (Ruff/Black/mypy/
  pytest/pre-commit), pydantic-settings config, structlog logging, docker-compose
  skeleton (PostGIS + Redis).
- **M1 — City data layer**: OSMnx ingest of central Riyadh → cached graph + POIs.
- **M2 — Simulation core**: agents, real-network routing, schedule FSM, weather,
  events, world clock.
- **M3 — Persistence**: SQLAlchemy + PostGIS models, repositories, Redis live
  state; Docker services online.
- **M4 — API**: FastAPI REST + WebSocket live streaming.
- **M5 — Frontend**: React/TS/Vite/MapLibre/Tailwind live map.
- **M6 — Scale & polish**: spatial batching, CI, seed scenarios, docs.

Each milestone compiles, runs, and ships tests before the next begins.
