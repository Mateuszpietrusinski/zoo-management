"""Unit tests for Zoo, Enclosure, FeedingSchedule."""

from datetime import time

from zoo_management.domain.entities import (
    Enclosure,
    EnclosureType,
    FeedingSchedule,
    Lion,
    Origin,
    Zoo,
)


def test_zoo_creation_with_tour_route() -> None:
    """Zoo is created with id, name, and tour_route."""
    zoo = Zoo("zoo-1", "City Zoo", ["enc-1", "enc-2"])
    assert zoo.id == "zoo-1"
    assert zoo.name == "City Zoo"
    assert zoo.tour_route == ["enc-1", "enc-2"]


def test_zoo_repr_str_eq() -> None:
    """Zoo has __repr__, __str__, __eq__ by id."""
    zoo1 = Zoo("zoo-1", "City Zoo", [])
    assert "zoo-1" in repr(zoo1)
    assert "City Zoo" in repr(zoo1)
    assert "City Zoo" in str(zoo1)
    zoo2 = Zoo("zoo-1", "Other", [])
    assert zoo1 == zoo2
    zoo3 = Zoo("zoo-2", "City Zoo", [])
    assert zoo1 != zoo3


def test_enclosure_creation_with_type_and_zoo_id() -> None:
    """Enclosure is created with id, name, type, zoo_id."""
    enc = Enclosure("enc-1", "Mammal House", EnclosureType.MAMMAL, "zoo-1")
    assert enc.id == "enc-1"
    assert enc.name == "Mammal House"
    assert enc.enclosure_type == EnclosureType.MAMMAL
    assert enc.zoo_id == "zoo-1"


def test_enclosure_animals_defaults_to_empty_list() -> None:
    """Enclosure.animals defaults to empty list when not provided."""
    enc = Enclosure("enc-1", "Mammal House", EnclosureType.MAMMAL, "zoo-1")
    assert enc.animals == []


def test_enclosure_is_occupied_false_when_no_animals() -> None:
    """Enclosure.is_occupied is False when no animals."""
    enc = Enclosure("enc-1", "Mammal House", EnclosureType.MAMMAL, "zoo-1")
    assert enc.is_occupied is False


def test_enclosure_is_occupied_true_when_animals_present() -> None:
    """Enclosure.is_occupied is True when animals are present."""
    enc = Enclosure("enc-1", "Mammal House", EnclosureType.MAMMAL, "zoo-1")
    enc.animals.append(Lion("a1", "Simba", Origin.INTERNAL))
    assert enc.is_occupied is True


def test_enclosure_animal_count_matches_list_length() -> None:
    """Enclosure.animal_count matches len(animals)."""
    enc = Enclosure("enc-1", "Mammal House", EnclosureType.MAMMAL, "zoo-1")
    assert enc.animal_count == 0
    enc.animals.append(Lion("a1", "Simba", Origin.INTERNAL))
    assert enc.animal_count == 1


def test_enclosure_assigned_zookeeper_id_defaults_to_none() -> None:
    """Enclosure.assigned_zookeeper_id defaults to None."""
    enc = Enclosure("enc-1", "Mammal House", EnclosureType.MAMMAL, "zoo-1")
    assert enc.assigned_zookeeper_id is None


def test_enclosure_repr_str_eq() -> None:
    """Enclosure has __repr__, __str__, __eq__ by id."""
    enc1 = Enclosure("enc-1", "Mammal House", EnclosureType.MAMMAL, "zoo-1")
    assert "enc-1" in repr(enc1)
    assert "Mammal House" in repr(enc1)
    assert "Mammal House" in str(enc1)
    enc2 = Enclosure("enc-1", "Other", EnclosureType.BIRD, "zoo-2")
    assert enc1 == enc2
    enc3 = Enclosure("enc-2", "Mammal House", EnclosureType.MAMMAL, "zoo-1")
    assert enc1 != enc3


def test_feeding_schedule_creation() -> None:
    """FeedingSchedule is created with id, enclosure_id, scheduled_time, diet."""
    sched = FeedingSchedule("s1", "enc-1", time(9, 0), "meat")
    assert sched.id == "s1"
    assert sched.enclosure_id == "enc-1"
    assert sched.scheduled_time == time(9, 0)
    assert sched.diet == "meat"


def test_feeding_schedule_schedule_info_property() -> None:
    """FeedingSchedule.schedule_info returns formatted summary."""
    sched = FeedingSchedule("s1", "enc-1", time(9, 0), "meat")
    info = sched.schedule_info
    assert "enc-1" in info
    assert "09:00" in info or "9" in info
    assert "meat" in info


def test_feeding_schedule_repr_str() -> None:
    """FeedingSchedule has __repr__ and __str__."""
    sched = FeedingSchedule("s1", "enc-1", time(9, 0), "meat")
    assert "s1" in repr(sched)
    assert "s1" in str(sched) or "enc-1" in str(sched)
