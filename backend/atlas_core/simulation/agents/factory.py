"""Population generation.

Builds a realistic population of :class:`Citizen` agents from a
:class:`~atlas_core.city.model.CityModel`: each citizen is housed in a real
residential building, assigned an age-appropriate occupation and a workplace of
the matching category, and given a preferred transport mode. Generation is fully
seeded so a given ``(city, seed, size)`` always yields the same population.
"""

from __future__ import annotations

import random

from atlas_core.city.categories import BuildingCategory, PoiCategory
from atlas_core.city.model import CityModel
from atlas_core.city.types import Building, Poi
from atlas_core.simulation.agents.citizen import Citizen
from atlas_core.simulation.types import Destination, Occupation, TransportMode

# Occupation -> the POI category a worker of that type commutes to. Occupations
# absent here either work in offices (handled specially) or stay home.
_WORKPLACE_POI: dict[Occupation, PoiCategory] = {
    Occupation.HEALTHCARE_WORKER: PoiCategory.HOSPITAL,
    Occupation.RETAIL_WORKER: PoiCategory.MALL,
    Occupation.STUDENT: PoiCategory.UNIVERSITY,
    Occupation.CHILD: PoiCategory.SCHOOL,
}

# Preferred transport mix (approximate Riyadh modal split; car-dominant).
_TRANSPORT_WEIGHTS: dict[TransportMode, float] = {
    TransportMode.CAR: 0.68,
    TransportMode.METRO: 0.14,
    TransportMode.BUS: 0.10,
    TransportMode.WALK: 0.08,
}


class PopulationFactory:
    """Creates seeded populations bound to a specific city."""

    def __init__(self, city: CityModel, rng: random.Random) -> None:
        self._city = city
        self._rng = rng
        self._homes: list[Building] = (
            city.buildings_of(BuildingCategory.RESIDENTIAL) or city.buildings
        )
        self._offices: list[Building] = city.buildings_of(BuildingCategory.OFFICE) or self._homes
        if not self._homes:
            raise ValueError("city has no buildings to house a population")

    def create(self, size: int) -> list[Citizen]:
        """Create ``size`` citizens."""
        if size < 1:
            raise ValueError("population size must be at least 1")
        return [self._create_one(i) for i in range(size)]

    def _create_one(self, citizen_id: int) -> Citizen:
        age = self._sample_age()
        occupation = self._occupation_for_age(age)
        home = self._to_destination(self._rng.choice(self._homes), fallback_label="home")
        workplace = self._workplace_for(occupation)
        transport = self._sample_transport()

        return Citizen(
            id=citizen_id,
            age=age,
            occupation=occupation,
            home=home,
            workplace=workplace,
            preferred_transport=transport,
            position=home.location,
            current_node=home.node,
            prayer_propensity=round(self._rng.random(), 3),
            energy=round(self._rng.uniform(70.0, 100.0), 1),
            happiness=round(self._rng.uniform(55.0, 85.0), 1),
        )

    # -- Sampling helpers ----------------------------------------------------

    def _sample_age(self) -> int:
        """Sample an age from broad, Riyadh-plausible bands."""
        band = self._rng.choices(
            population=[(0, 12), (13, 18), (19, 24), (25, 44), (45, 64), (65, 85)],
            weights=[0.20, 0.11, 0.12, 0.34, 0.16, 0.07],
            k=1,
        )[0]
        return self._rng.randint(band[0], band[1])

    def _occupation_for_age(self, age: int) -> Occupation:
        if age < 6:
            return Occupation.CHILD
        if age < 19:
            return Occupation.CHILD if age < 13 else Occupation.STUDENT
        if age < 25:
            return Occupation.STUDENT
        if age >= 65:
            return Occupation.RETIRED
        return self._rng.choices(
            population=[
                Occupation.OFFICE_WORKER,
                Occupation.HEALTHCARE_WORKER,
                Occupation.RETAIL_WORKER,
            ],
            weights=[0.6, 0.15, 0.25],
            k=1,
        )[0]

    def _sample_transport(self) -> TransportMode:
        modes = list(_TRANSPORT_WEIGHTS.keys())
        weights = list(_TRANSPORT_WEIGHTS.values())
        return self._rng.choices(modes, weights=weights, k=1)[0]

    def _workplace_for(self, occupation: Occupation) -> Destination | None:
        if occupation == Occupation.RETIRED:
            return None
        if occupation == Occupation.OFFICE_WORKER:
            return self._to_destination(self._rng.choice(self._offices), fallback_label="office")

        category = _WORKPLACE_POI.get(occupation)
        if category is not None:
            pois = self._city.pois_of(category)
            if pois:
                return self._poi_destination(self._rng.choice(pois))
        # Fallback: an office building keeps everyone employed even if a POI
        # category is sparse in the current extract.
        return self._to_destination(self._rng.choice(self._offices), fallback_label="workplace")

    # -- Conversion helpers --------------------------------------------------

    def _to_destination(self, building: Building, *, fallback_label: str) -> Destination:
        return Destination(
            location=building.centroid,
            node=building.nearest_node,
            label=building.name or f"{fallback_label}#{building.id}",
        )

    def _poi_destination(self, poi: Poi) -> Destination:
        return Destination(
            location=poi.location,
            node=poi.nearest_node,
            label=poi.name or f"{poi.category.value}#{poi.id}",
        )
