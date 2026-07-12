# Atlas

Atlas is an AI-powered digital twin platform that simulates real cities. The
first supported city is **Riyadh, Saudi Arabia**.

Atlas models a living city — citizens, buildings, roads, traffic, weather,
events, businesses, and public transport — on top of **real OpenStreetMap
data**. Citizens are autonomous agents that move along the actual road network
via shortest paths (never in straight lines), following daily routines that
respond to weather and city events. The city evolves continuously over time and
streams live to an interactive map.

## Tech stack

**Backend:** Python 3.13 · FastAPI · OSMnx · GeoPandas · NetworkX · Shapely ·
Pydantic · SQLAlchemy · PostgreSQL + PostGIS · Redis · WebSockets

**Frontend:** React · TypeScript · Vite · MapLibre GL JS · TailwindCSS

**Dev:** Docker · Docker Compose · pytest · Ruff · Black · mypy · pre-commit

## Project layout

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full design. In short:

```
backend/       Python workspace (atlas_core engine + api layer)
frontend/      React app (Milestone 5)
docs/          Architecture and runbooks
legacy/        Archived Streamlit prototype (reference only)
docker-compose.yml
```

## Getting started (development)

```bash
# 1. Backend environment
python3.13 -m venv .venv && source .venv/bin/activate
pip install -e "backend/[dev]"

# 2. Data services (PostGIS + Redis) — needed from Milestone 3 onward
docker compose up -d postgres redis

# 3. Copy environment defaults
cp .env.example .env

# 4. Quality gate
cd backend
pytest            # tests
ruff check .      # lint
black --check .   # format
mypy atlas_core   # types
```

## Status

| Milestone | Scope | State |
|-----------|-------|-------|
| M0 | Foundation, tooling, config, logging, compose skeleton | ✅ Done |
| M1 | City data layer (OSMnx ingest + cache) | ⏳ Next |
| M2 | Simulation core (agents, routing, weather, events) | ◻️ |
| M3 | Persistence (PostGIS + Redis) | ◻️ |
| M4 | API (FastAPI REST + WebSocket) | ◻️ |
| M5 | Frontend (React + MapLibre) | ◻️ |
| M6 | Scale & polish | ◻️ |
