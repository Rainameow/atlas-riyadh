from __future__ import annotations

import math
import random
from collections import Counter
from typing import Iterable

import pandas as pd

from .config import DEFAULT_POPULATION, DEFAULT_SPEED, RANDOM_SEED
from .data import DISTRICTS, EVENT_PRESETS, WEATHER_PRESETS
from .models import Citizen, District


class CitySimulation:
    def __init__(
        self,
        population: int = DEFAULT_POPULATION,
        seed: int = RANDOM_SEED,
    ) -> None:
        if population < 1:
            raise ValueError("population must be at least 1")

        self.random = random.Random(seed)
        self.hour = 6
        self.weather = "Clear"
        self.event = "None"
        self.tick_count = 0

        self.districts = {
            item["name"]: District(
                name=item["name"],
                lat=item["lat"],
                lon=item["lon"],
                district_type=item["type"],
            )
            for item in DISTRICTS
        }
        self.citizens = self._create_population(population)

    def _district_names_by_type(self, district_type: str) -> list[str]:
        return [
            district.name
            for district in self.districts.values()
            if district.district_type == district_type
        ]

    def _create_population(self, population: int) -> list[Citizen]:
        homes = self._district_names_by_type("residential")
        workplaces = (
            self._district_names_by_type("business")
            + self._district_names_by_type("education")
        )
        leisure = self._district_names_by_type("leisure")

        citizens: list[Citizen] = []
        for citizen_id in range(population):
            home = self.random.choice(homes)
            work = self.random.choice(workplaces)
            fun = self.random.choice(leisure)
            citizens.append(
                Citizen(
                    citizen_id=citizen_id,
                    home=home,
                    work=work,
                    leisure=fun,
                    current_district=home,
                    destination=home,
                )
            )
        return citizens

    def set_conditions(self, weather: str, event: str) -> None:
        if weather not in WEATHER_PRESETS:
            raise ValueError(f"unknown weather: {weather}")
        if event not in EVENT_PRESETS:
            raise ValueError(f"unknown event: {event}")
        self.weather = weather
        self.event = event

    def _choose_destination_with_event(self, citizen: Citizen) -> str:
        base_destination = citizen.choose_destination(self.hour)
        event_data = EVENT_PRESETS[self.event]
        target = event_data["target"]
        pull = float(event_data["pull"])

        if target is None:
            return base_destination

        if pull > 0 and self.random.random() < pull:
            return target

        if pull < 0 and base_destination == target:
            alternatives = [name for name in self.districts if name != target]
            return self.random.choice(alternatives)

        return base_destination

    def _effective_speed(self) -> float:
        weather_factor = float(WEATHER_PRESETS[self.weather]["speed_multiplier"])
        event_factor = float(EVENT_PRESETS[self.event]["congestion"])
        return DEFAULT_SPEED * weather_factor * event_factor

    def step(self, minutes: int = 30) -> None:
        if minutes <= 0:
            raise ValueError("minutes must be positive")

        self.tick_count += 1
        self.hour = (self.hour + minutes / 60) % 24
        speed = self._effective_speed() * (minutes / 30)

        for citizen in self.citizens:
            next_destination = self._choose_destination_with_event(citizen)

            if citizen.destination != next_destination:
                citizen.destination = next_destination
                citizen.progress = 0.0

            if citizen.current_district == citizen.destination:
                citizen.progress = 1.0
                continue

            citizen.progress = min(1.0, citizen.progress + speed)

            if citizen.progress >= 1.0:
                citizen.current_district = citizen.destination

    def _interpolate_position(self, citizen: Citizen) -> tuple[float, float]:
        start = self.districts[citizen.current_district]
        end = self.districts[citizen.destination]

        if citizen.current_district == citizen.destination:
            jitter_lat = self.random.uniform(-0.004, 0.004)
            jitter_lon = self.random.uniform(-0.004, 0.004)
            return start.lat + jitter_lat, start.lon + jitter_lon

        progress = citizen.progress
        lat = start.lat + (end.lat - start.lat) * progress
        lon = start.lon + (end.lon - start.lon) * progress
        return lat, lon

    def citizens_frame(self) -> pd.DataFrame:
        rows = []
        for citizen in self.citizens:
            lat, lon = self._interpolate_position(citizen)
            rows.append(
                {
                    "citizen_id": citizen.citizen_id,
                    "lat": lat,
                    "lon": lon,
                    "current_district": citizen.current_district,
                    "destination": citizen.destination,
                    "progress": round(citizen.progress, 3),
                }
            )
        return pd.DataFrame(rows)

    def district_activity_frame(self) -> pd.DataFrame:
        counts = Counter(c.destination for c in self.citizens)
        rows = []
        for district in self.districts.values():
            rows.append(
                {
                    "district": district.name,
                    "type": district.district_type,
                    "lat": district.lat,
                    "lon": district.lon,
                    "activity": counts[district.name],
                }
            )
        return pd.DataFrame(rows).sort_values("activity", ascending=False)

    def metrics(self) -> dict[str, float | int | str]:
        traveling = sum(
            citizen.current_district != citizen.destination
            for citizen in self.citizens
        )
        leisure = sum(
            self.districts[citizen.destination].district_type == "leisure"
            for citizen in self.citizens
        )
        return {
            "population": len(self.citizens),
            "traveling": traveling,
            "leisure_trips": leisure,
            "hour": round(self.hour, 1),
            "weather": self.weather,
            "event": self.event,
        }
