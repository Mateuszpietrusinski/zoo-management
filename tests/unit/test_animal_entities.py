"""Unit tests for Animal hierarchy (ABC → mid-tier → concrete)."""

import pytest

from zoo_management.domain.entities import (
    Animal,
    Bird,
    Crocodile,
    Eagle,
    Elephant,
    Lion,
    Mammal,
    Monkey,
    Origin,
    Penguin,
    Reptile,
)


def test_cannot_instantiate_animal_directly() -> None:
    """Animal is abstract and cannot be instantiated."""
    with pytest.raises(TypeError):
        Animal("a1", "Bob", Origin.INTERNAL)  # type: ignore[abstract]


def test_cannot_instantiate_mammal_directly() -> None:
    """Mammal is abstract and cannot be instantiated."""
    with pytest.raises(TypeError):
        Mammal("a1", "Bob", Origin.INTERNAL)  # type: ignore[abstract]


def test_cannot_instantiate_bird_directly() -> None:
    """Bird is abstract and cannot be instantiated."""
    with pytest.raises(TypeError):
        Bird("a1", "Bob", Origin.INTERNAL)  # type: ignore[abstract]


def test_cannot_instantiate_reptile_directly() -> None:
    """Reptile is abstract and cannot be instantiated."""
    with pytest.raises(TypeError):
        Reptile("a1", "Bob", Origin.INTERNAL)  # type: ignore[abstract]


def test_lion_get_diet_type_returns_carnivore() -> None:
    """Lion.get_diet_type returns 'carnivore'."""
    lion = Lion("a1", "Simba", Origin.INTERNAL)
    assert lion.get_diet_type() == "carnivore"


def test_elephant_get_diet_type_returns_herbivore() -> None:
    """Elephant.get_diet_type returns 'herbivore'."""
    elephant = Elephant("a1", "Dumbo", Origin.INTERNAL)
    assert elephant.get_diet_type() == "herbivore"


def test_monkey_get_diet_type_returns_omnivore() -> None:
    """Monkey.get_diet_type returns 'omnivore'."""
    monkey = Monkey("a1", "George", Origin.INTERNAL)
    assert monkey.get_diet_type() == "omnivore"


def test_eagle_get_diet_type_returns_carnivore() -> None:
    """Eagle.get_diet_type returns 'carnivore'."""
    eagle = Eagle("a1", "Sky", Origin.INTERNAL)
    assert eagle.get_diet_type() == "carnivore"


def test_penguin_get_diet_type_returns_piscivore() -> None:
    """Penguin.get_diet_type returns 'piscivore'."""
    penguin = Penguin("a1", "Pingu", Origin.INTERNAL)
    assert penguin.get_diet_type() == "piscivore"


def test_crocodile_get_diet_type_returns_carnivore() -> None:
    """Crocodile.get_diet_type returns 'carnivore'."""
    croc = Crocodile("a1", "Snappy", Origin.INTERNAL)
    assert croc.get_diet_type() == "carnivore"


def test_lion_type_name_returns_lion() -> None:
    """Lion.type_name property returns 'Lion'."""
    lion = Lion("a1", "Simba", Origin.INTERNAL)
    assert lion.type_name == "Lion"


def test_lion_taxonomic_type_returns_mammal() -> None:
    """Lion.taxonomic_type returns 'Mammal'."""
    lion = Lion("a1", "Simba", Origin.INTERNAL)
    assert lion.taxonomic_type == "Mammal"


def test_penguin_taxonomic_type_returns_bird() -> None:
    """Penguin.taxonomic_type returns 'Bird'."""
    penguin = Penguin("a1", "Pingu", Origin.INTERNAL)
    assert penguin.taxonomic_type == "Bird"


def test_crocodile_taxonomic_type_returns_reptile() -> None:
    """Crocodile.taxonomic_type returns 'Reptile'."""
    croc = Crocodile("a1", "Snappy", Origin.INTERNAL)
    assert croc.taxonomic_type == "Reptile"


def test_animal_is_placed_false_when_no_enclosure() -> None:
    """Animal.is_placed is False when enclosure_id is None."""
    lion = Lion("a1", "Simba", Origin.INTERNAL, enclosure_id=None)
    assert lion.is_placed is False


def test_animal_is_placed_true_when_enclosure_set() -> None:
    """Animal.is_placed is True when enclosure_id is set."""
    lion = Lion("a1", "Simba", Origin.INTERNAL, enclosure_id="enc-1")
    assert lion.is_placed is True


def test_animal_repr_contains_id_and_name() -> None:
    """Animal __repr__ contains id and name."""
    lion = Lion("a1", "Simba", Origin.INTERNAL)
    r = repr(lion)
    assert "a1" in r and "Simba" in r


def test_animal_str_contains_name() -> None:
    """Animal __str__ contains name."""
    lion = Lion("a1", "Simba", Origin.INTERNAL)
    assert "Simba" in str(lion)


def test_animal_eq_by_id() -> None:
    """Two animals with same id are equal."""
    lion1 = Lion("a1", "Simba", Origin.INTERNAL)
    lion2 = Lion("a1", "Other", Origin.EXTERNAL)
    assert lion1 == lion2


def test_animal_eq_different_id_not_equal() -> None:
    """Two animals with different ids are not equal."""
    lion1 = Lion("a1", "Simba", Origin.INTERNAL)
    lion2 = Lion("a2", "Simba", Origin.INTERNAL)
    assert lion1 != lion2
