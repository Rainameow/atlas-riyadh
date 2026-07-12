import pytest

from atlas.simulation import CitySimulation


def test_population_size_is_respected():
    simulation = CitySimulation(population=120)
    assert len(simulation.citizens) == 120


def test_invalid_population_raises_error():
    with pytest.raises(ValueError):
        CitySimulation(population=0)


def test_step_advances_time():
    simulation = CitySimulation(population=50)
    start_hour = simulation.hour
    simulation.step(minutes=60)
    assert simulation.hour == start_hour + 1


def test_weather_changes_effective_speed():
    simulation = CitySimulation(population=50)
    simulation.set_conditions("Clear", "None")
    clear_speed = simulation._effective_speed()

    simulation.set_conditions("Sandstorm", "None")
    sandstorm_speed = simulation._effective_speed()

    assert sandstorm_speed < clear_speed


def test_unknown_condition_is_rejected():
    simulation = CitySimulation(population=10)

    with pytest.raises(ValueError):
        simulation.set_conditions("Snowstorm", "None")


def test_frames_have_expected_columns():
    simulation = CitySimulation(population=20)

    citizen_columns = set(simulation.citizens_frame().columns)
    district_columns = set(simulation.district_activity_frame().columns)

    assert {"citizen_id", "lat", "lon", "destination"}.issubset(citizen_columns)
    assert {"district", "type", "activity"}.issubset(district_columns)
