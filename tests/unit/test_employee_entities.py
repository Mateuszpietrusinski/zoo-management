"""Unit tests for Employee hierarchy (ABC → concrete)."""

import pytest

from zoo_management.domain.entities import Employee, Guide, Veterinarian, Zookeeper


def test_cannot_instantiate_employee_directly() -> None:
    """Employee is abstract and cannot be instantiated."""
    with pytest.raises(TypeError):
        Employee("e1", "Alice", "zoo-1")  # type: ignore[abstract]


def test_zookeeper_role_returns_zookeeper() -> None:
    """Zookeeper.role returns 'Zookeeper'."""
    zk = Zookeeper("e1", "Alice", "zoo-1")
    assert zk.role == "Zookeeper"


def test_veterinarian_role_returns_veterinarian() -> None:
    """Veterinarian.role returns 'Veterinarian'."""
    vet = Veterinarian("e1", "Dr. Bob", "zoo-1")
    assert vet.role == "Veterinarian"


def test_guide_role_returns_guide() -> None:
    """Guide.role returns 'Guide'."""
    guide = Guide("e1", "Carol", "zoo-1")
    assert guide.role == "Guide"


def test_guide_is_available_defaults_to_true() -> None:
    """Guide.is_available defaults to True."""
    guide = Guide("e1", "Carol", "zoo-1")
    assert guide.is_available is True


def test_guide_is_available_can_be_set_false() -> None:
    """Guide.is_available can be set to False."""
    guide = Guide("e1", "Carol", "zoo-1", is_available=False)
    assert guide.is_available is False


def test_employee_repr_contains_id_and_name() -> None:
    """Employee __repr__ contains id and name."""
    zk = Zookeeper("e1", "Alice", "zoo-1")
    r = repr(zk)
    assert "e1" in r and "Alice" in r


def test_employee_str_contains_name() -> None:
    """Employee __str__ contains name."""
    zk = Zookeeper("e1", "Alice", "zoo-1")
    assert "Alice" in str(zk)


def test_employee_eq_by_id() -> None:
    """Two employees with same id are equal."""
    zk1 = Zookeeper("e1", "Alice", "zoo-1")
    vet1 = Veterinarian("e1", "Bob", "zoo-2")
    assert zk1 == vet1
