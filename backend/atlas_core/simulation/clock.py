"""Simulation world clock.

Tracks simulated time as it advances in fixed-size ticks. The clock is the sole
authority on "what time is it in the city", which the scheduler consults to
decide what every citizen should be doing.
"""

from __future__ import annotations

from dataclasses import dataclass

_MINUTES_PER_DAY = 24 * 60
_DAYS = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")


@dataclass
class SimulationClock:
    """A monotonic simulated clock advanced in discrete ticks.

    Attributes:
        minutes_per_tick: Simulated minutes elapsed per :meth:`tick`.
        total_minutes: Minutes elapsed since the start of the simulation.
    """

    minutes_per_tick: int = 5
    total_minutes: int = 0

    def tick(self) -> None:
        """Advance the clock by one tick."""
        self.total_minutes += self.minutes_per_tick

    @property
    def tick_count(self) -> int:
        return self.total_minutes // self.minutes_per_tick if self.minutes_per_tick else 0

    @property
    def minute_of_day(self) -> int:
        """Minutes since midnight (0..1439)."""
        return self.total_minutes % _MINUTES_PER_DAY

    @property
    def hour(self) -> int:
        """Hour of day (0..23)."""
        return self.minute_of_day // 60

    @property
    def minute(self) -> int:
        """Minute within the current hour (0..59)."""
        return self.minute_of_day % 60

    @property
    def hour_of_day(self) -> float:
        """Fractional hour of day, e.g. 13.5 at 13:30."""
        return self.minute_of_day / 60.0

    @property
    def day_index(self) -> int:
        """Whole days elapsed since the start (day 0 is the first day)."""
        return self.total_minutes // _MINUTES_PER_DAY

    @property
    def day_name(self) -> str:
        """Weekday name; the simulation starts on a Sunday (Riyadh work week)."""
        return _DAYS[self.day_index % 7]

    @property
    def is_weekend(self) -> bool:
        """Riyadh's weekend is Friday and Saturday."""
        return self.day_name in {"Friday", "Saturday"}

    def clock_label(self) -> str:
        """Return a ``HH:MM`` label for the current time."""
        return f"{self.hour:02d}:{self.minute:02d}"
