"""Weather subsystem.

Riyadh's weather shifts citizen behaviour: sandstorms and heatwaves suppress
outdoor activity and slow traffic; rain slows roads and pushes people indoors.
The :class:`WeatherSystem` owns the current :class:`WeatherState` and evolves it
day to day, while allowing manual override (used by the API and scenarios).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from enum import StrEnum


class WeatherCondition(StrEnum):
    CLEAR = "clear"
    RAIN = "rain"
    HEATWAVE = "heatwave"
    SANDSTORM = "sandstorm"


@dataclass(frozen=True, slots=True)
class WeatherEffects:
    """How a weather condition scales behaviour.

    Attributes:
        speed_factor: Multiplier applied to travel speed (1.0 == unaffected).
        outdoor_factor: Multiplier on the likelihood of choosing an outdoor
            activity (1.0 == unaffected, 0.0 == avoided entirely).
        base_temp_c: Representative midday temperature for the condition.
    """

    speed_factor: float
    outdoor_factor: float
    base_temp_c: float


_EFFECTS: dict[WeatherCondition, WeatherEffects] = {
    WeatherCondition.CLEAR: WeatherEffects(speed_factor=1.0, outdoor_factor=1.0, base_temp_c=32.0),
    WeatherCondition.RAIN: WeatherEffects(speed_factor=0.70, outdoor_factor=0.35, base_temp_c=20.0),
    WeatherCondition.HEATWAVE: WeatherEffects(
        speed_factor=0.90, outdoor_factor=0.25, base_temp_c=46.0
    ),
    WeatherCondition.SANDSTORM: WeatherEffects(
        speed_factor=0.50, outdoor_factor=0.10, base_temp_c=38.0
    ),
}

# Daily transition weights (Riyadh is overwhelmingly clear and hot).
_DAILY_WEIGHTS: dict[WeatherCondition, float] = {
    WeatherCondition.CLEAR: 0.70,
    WeatherCondition.HEATWAVE: 0.18,
    WeatherCondition.SANDSTORM: 0.08,
    WeatherCondition.RAIN: 0.04,
}


@dataclass(frozen=True, slots=True)
class WeatherState:
    """The city's weather at a moment in time."""

    condition: WeatherCondition
    temperature_c: float

    @property
    def effects(self) -> WeatherEffects:
        return _EFFECTS[self.condition]

    @property
    def speed_factor(self) -> float:
        return self.effects.speed_factor

    @property
    def outdoor_factor(self) -> float:
        return self.effects.outdoor_factor


class WeatherSystem:
    """Owns and evolves the city's weather.

    Args:
        rng: Seeded random generator (shared with the world for determinism).
        initial: Starting condition; defaults to clear.
    """

    def __init__(
        self, rng: random.Random, initial: WeatherCondition = WeatherCondition.CLEAR
    ) -> None:
        self._rng = rng
        self._condition = initial
        self._forced = False
        self._current_day = 0

    @property
    def state(self) -> WeatherState:
        return self._state_for(self._condition, hour=12.0)

    def state_at(self, hour_of_day: float) -> WeatherState:
        """Return weather at a given hour, applying diurnal temperature drift."""
        return self._state_for(self._condition, hour=hour_of_day)

    def _state_for(self, condition: WeatherCondition, hour: float) -> WeatherState:
        base = _EFFECTS[condition].base_temp_c
        # Simple diurnal curve: coolest ~05:00, warmest ~15:00, +/- 8 degrees.
        drift = -8.0 * math.cos((hour - 5.0) / 24.0 * 2 * math.pi)
        return WeatherState(condition=condition, temperature_c=round(base + drift, 1))

    def force(self, condition: WeatherCondition) -> None:
        """Pin the weather to a condition until :meth:`clear_override`."""
        self._condition = condition
        self._forced = True

    def clear_override(self) -> None:
        """Resume automatic day-to-day weather evolution."""
        self._forced = False

    def update(self, day_index: int) -> None:
        """Advance the weather; may pick a new condition at each new day."""
        if self._forced or day_index == self._current_day:
            return
        self._current_day = day_index
        conditions = list(_DAILY_WEIGHTS.keys())
        weights = list(_DAILY_WEIGHTS.values())
        self._condition = self._rng.choices(conditions, weights=weights, k=1)[0]
