"""Atlas simulation engine.

A pure-Python, framework-free engine: a :class:`World` owns a city, a population
of autonomous :class:`Citizen` agents, and the clock/weather/event subsystems,
and advances them one tick at a time.
"""

from atlas_core.simulation.agents import Citizen, PopulationFactory
from atlas_core.simulation.clock import SimulationClock
from atlas_core.simulation.events import CityEvent, EventSystem, EventType
from atlas_core.simulation.types import Activity, Occupation, TransportMode
from atlas_core.simulation.weather import WeatherCondition, WeatherState, WeatherSystem
from atlas_core.simulation.world import CitizenSnapshot, World

__all__ = [
    "Activity",
    "Citizen",
    "CitizenSnapshot",
    "CityEvent",
    "EventSystem",
    "EventType",
    "Occupation",
    "PopulationFactory",
    "SimulationClock",
    "TransportMode",
    "WeatherCondition",
    "WeatherState",
    "WeatherSystem",
    "World",
]
