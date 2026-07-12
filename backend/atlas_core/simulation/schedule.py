"""Daily routine scheduling.

Given the world clock and a citizen's profile, :func:`scheduled_activity`
decides what that citizen *intends* to do right now — the activity the behaviour
layer then turns into a concrete destination. The routine covers the full brief:
sleep, prayer, commute/work, meals, shopping, exercise, socialising, and
returning home, on a Riyadh work week (Sunday to Thursday) with the five daily
prayers woven in.
"""

from __future__ import annotations

from dataclasses import dataclass

from atlas_core.simulation.agents.citizen import Citizen
from atlas_core.simulation.clock import SimulationClock
from atlas_core.simulation.types import Activity, Occupation


@dataclass(frozen=True, slots=True)
class WorkWindow:
    start: int  # minute of day
    end: int


# Working hours by occupation (minute-of-day). Absent occupations do not work.
_WORK_HOURS: dict[Occupation, WorkWindow] = {
    Occupation.OFFICE_WORKER: WorkWindow(8 * 60, 17 * 60),
    Occupation.HEALTHCARE_WORKER: WorkWindow(8 * 60, 17 * 60),
    Occupation.RETAIL_WORKER: WorkWindow(10 * 60, 22 * 60),
    Occupation.STUDENT: WorkWindow(8 * 60, 14 * 60),
    Occupation.CHILD: WorkWindow(7 * 60 + 30, 14 * 60),
}

# Approximate Riyadh prayer times (minute-of-day) and the window each occupies.
_PRAYER_TIMES: tuple[int, ...] = (
    5 * 60,  # Fajr   05:00
    12 * 60 + 15,  # Dhuhr  12:15
    15 * 60 + 30,  # Asr    15:30
    18 * 60 + 30,  # Maghrib 18:30
    20 * 60 + 15,  # Isha   20:15
)
_PRAYER_WINDOW_MIN = 25

_SLEEP_START = 22 * 60 + 30  # 22:30
_SLEEP_END = 5 * 60  # 05:00
_LUNCH = (13 * 60, 14 * 60)
_DINNER = (19 * 60, 20 * 60 + 30)
_EVENING_LEISURE = (20 * 60 + 30, 22 * 60 + 30)

_LEISURE_CHOICES: tuple[Activity, ...] = (
    Activity.SHOP,
    Activity.SOCIALIZE,
    Activity.EXERCISE,
    Activity.EAT,
)


def in_prayer_window(minute_of_day: int) -> bool:
    """Whether the current minute falls in one of the five prayer windows."""
    return any(t <= minute_of_day < t + _PRAYER_WINDOW_MIN for t in _PRAYER_TIMES)


def scheduled_activity(clock: SimulationClock, citizen: Citizen) -> Activity:
    """Return the activity a citizen intends to pursue at the current time."""
    minute = clock.minute_of_day
    weekend = clock.is_weekend

    # 1. Prayer takes precedence for observant citizens (and Friday Jumua pulls
    #    strongly at Dhuhr).
    if in_prayer_window(minute) and _observes_this_prayer(citizen, minute, weekend):
        return Activity.PRAY

    # 2. Overnight sleep.
    if minute >= _SLEEP_START or minute < _SLEEP_END:
        return Activity.SLEEP

    # 3. Work / school on weekdays.
    if not weekend:
        window = _WORK_HOURS.get(citizen.occupation)
        working = (
            window is not None
            and citizen.workplace is not None
            and window.start <= minute < window.end
        )
        if working:
            # Lunch break carved out of the workday.
            if _in(minute, _LUNCH):
                return Activity.EAT
            return Activity.WORK

    # 4. Dinner.
    if _in(minute, _DINNER):
        return Activity.EAT

    # 5. Evening leisure.
    if _in(minute, _EVENING_LEISURE):
        return _leisure_choice(citizen, clock.day_index)

    # 6. Default: be at home.
    return Activity.HOME


def _observes_this_prayer(citizen: Citizen, minute: int, weekend: bool) -> bool:
    # Friday midday prayer (Jumua) is observed by almost everyone.
    if weekend and _PRAYER_TIMES[1] <= minute < _PRAYER_TIMES[1] + _PRAYER_WINDOW_MIN:
        return citizen.prayer_propensity > 0.1
    return citizen.prayer_propensity >= 0.5


def _leisure_choice(citizen: Citizen, day_index: int) -> Activity:
    # Deterministic per (citizen, day) so the choice is stable within a day but
    # varies day to day — no per-tick flip-flopping.
    idx = (citizen.id * 31 + day_index * 17) % len(_LEISURE_CHOICES)
    return _LEISURE_CHOICES[idx]


def _in(minute: int, window: tuple[int, int]) -> bool:
    return window[0] <= minute < window[1]
