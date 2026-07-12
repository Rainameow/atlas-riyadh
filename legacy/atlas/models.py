from dataclasses import dataclass


@dataclass
class District:
    name: str
    lat: float
    lon: float
    district_type: str


@dataclass
class Citizen:
    citizen_id: int
    home: str
    work: str
    leisure: str
    current_district: str
    destination: str
    progress: float = 1.0

    def choose_destination(self, hour: int) -> str:
        if 7 <= hour < 9:
            return self.work
        if 9 <= hour < 17:
            return self.work
        if 17 <= hour < 22:
            return self.leisure
        return self.home
