"""Central application configuration.

Settings are loaded from environment variables (and an optional ``.env`` file)
via ``pydantic-settings``. Every layer of Atlas reads its configuration from the
single :class:`Settings` instance returned by :func:`get_settings`, so there is
one authoritative source of truth and no scattered ``os.getenv`` calls.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repository layout anchors. ``settings.py`` lives at
# ``backend/atlas_core/config/settings.py`` -> parents[2] == ``backend``.
BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"


class CitySettings(BaseSettings):
    """Geographic definition of the simulated city.

    Defaults describe central Riyadh. The bounding box intentionally covers a
    focused core during development (per the roadmap) and can be widened to the
    full metro without code changes.
    """

    model_config = SettingsConfigDict(env_prefix="ATLAS_CITY_")

    name: str = "Riyadh"
    country: str = "Saudi Arabia"

    center_lat: float = 24.7136
    center_lon: float = 46.6753

    # Bounding box for the initial (bounded) OSM ingest: central Riyadh.
    bbox_north: float = 24.78
    bbox_south: float = 24.62
    bbox_east: float = 46.78
    bbox_west: float = 46.60

    # OSMnx network type for the drivable road graph.
    network_type: str = "drive"

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        """Return the bounding box as ``(west, south, east, north)`` (lon/lat)."""
        return (self.bbox_west, self.bbox_south, self.bbox_east, self.bbox_north)


class DatabaseSettings(BaseSettings):
    """PostgreSQL + PostGIS connection settings (used from Milestone 3)."""

    model_config = SettingsConfigDict(env_prefix="ATLAS_DB_")

    host: str = "localhost"
    port: int = 5432
    user: str = "atlas"
    password: str = "atlas"
    name: str = "atlas"

    @property
    def url(self) -> str:
        """SQLAlchemy connection URL using the psycopg (v3) driver."""
        return (
            f"postgresql+psycopg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


class RedisSettings(BaseSettings):
    """Redis connection settings (used from Milestone 3)."""

    model_config = SettingsConfigDict(env_prefix="ATLAS_REDIS_")

    host: str = "localhost"
    port: int = 6379
    db: int = 0

    @property
    def url(self) -> str:
        return f"redis://{self.host}:{self.port}/{self.db}"


class SimulationSettings(BaseSettings):
    """Tunable parameters for the simulation engine (used from Milestone 2)."""

    model_config = SettingsConfigDict(env_prefix="ATLAS_SIM_")

    random_seed: int = 42
    default_population: int = 1000
    # Simulated minutes advanced per engine tick.
    minutes_per_tick: int = 5
    # Wall-clock seconds between broadcast ticks when running live.
    tick_interval_seconds: float = 1.0


class Settings(BaseSettings):
    """Top-level settings aggregating every configuration group."""

    model_config = SettingsConfigDict(
        env_prefix="ATLAS_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    log_json: bool = False

    data_dir: Path = DATA_DIR
    cache_dir: Path = CACHE_DIR

    city: CitySettings = Field(default_factory=CitySettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    simulation: SimulationSettings = Field(default_factory=SimulationSettings)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide :class:`Settings` singleton.

    Cached so configuration is parsed once. Call ``get_settings.cache_clear()``
    in tests that need to reload from a modified environment.
    """
    settings = Settings()
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    return settings
