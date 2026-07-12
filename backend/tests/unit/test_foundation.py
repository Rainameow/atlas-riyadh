"""Milestone 0 smoke tests: configuration and logging wiring."""

from __future__ import annotations

import structlog
from atlas_core.config import configure_logging, get_logger, get_settings
from atlas_core.config.settings import Settings


def test_settings_load_with_defaults() -> None:
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.city.name == "Riyadh"
    assert settings.simulation.random_seed == 42


def test_city_bbox_is_west_south_east_north_order() -> None:
    settings = get_settings()
    west, south, east, north = settings.city.bbox
    assert west < east
    assert south < north


def test_database_url_uses_psycopg_driver() -> None:
    url = get_settings().database.url
    assert url.startswith("postgresql+psycopg://")
    assert "/atlas" in url


def test_redis_url_shape() -> None:
    assert get_settings().redis.url == "redis://localhost:6379/0"


def test_settings_singleton_is_cached() -> None:
    assert get_settings() is get_settings()


def test_cache_dir_created(tmp_path, monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("ATLAS_CACHE_DIR", str(tmp_path / "cache"))
    settings = get_settings()
    assert settings.cache_dir.exists()
    get_settings.cache_clear()


def test_logging_configures_and_returns_bound_logger() -> None:
    configure_logging(level="DEBUG")
    logger = get_logger("atlas.test")
    # A configured structlog logger exposes bind() and the standard log methods.
    assert hasattr(logger, "bind")
    assert callable(logger.info)
    assert structlog.is_configured()
    # Should not raise.
    logger.info("smoke", milestone=0)
