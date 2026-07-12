"""Tests for population generation."""

from __future__ import annotations

import random

import pytest
from atlas_core.simulation.agents.factory import PopulationFactory
from atlas_core.simulation.types import Occupation


def test_population_size(sample_city) -> None:
    citizens = PopulationFactory(sample_city, random.Random(0)).create(50)
    assert len(citizens) == 50


def test_population_is_deterministic_for_a_seed(sample_city) -> None:
    a = PopulationFactory(sample_city, random.Random(3)).create(30)
    b = PopulationFactory(sample_city, random.Random(3)).create(30)
    assert [(c.age, c.occupation, c.preferred_transport) for c in a] == [
        (c.age, c.occupation, c.preferred_transport) for c in b
    ]


def test_size_below_one_raises(sample_city) -> None:
    with pytest.raises(ValueError):
        PopulationFactory(sample_city, random.Random(0)).create(0)


def test_occupation_matches_age_bands(sample_city) -> None:
    citizens = PopulationFactory(sample_city, random.Random(9)).create(300)
    for c in citizens:
        if c.occupation == Occupation.RETIRED:
            assert c.age >= 65
        if c.occupation == Occupation.CHILD:
            assert c.age < 19


def test_everyone_starts_at_a_real_node(sample_city) -> None:
    citizens = PopulationFactory(sample_city, random.Random(0)).create(20)
    valid_nodes = set(sample_city.network.node_ids)
    for c in citizens:
        assert c.current_node in valid_nodes
        assert c.position == c.home.location


def test_retired_have_no_workplace(sample_city) -> None:
    citizens = PopulationFactory(sample_city, random.Random(1)).create(200)
    retired = [c for c in citizens if c.occupation == Occupation.RETIRED]
    assert retired  # sample is large enough to contain some
    assert all(c.workplace is None for c in retired)
