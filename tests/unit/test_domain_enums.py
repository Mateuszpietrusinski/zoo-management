"""Unit tests for domain enums."""


from zoo_management.domain.entities import EnclosureType, HealthResult, Origin


def test_origin_enum_has_internal_and_external() -> None:
    """Origin enum has INTERNAL and EXTERNAL values."""
    assert Origin.INTERNAL.value == "internal"
    assert Origin.EXTERNAL.value == "external"


def test_enclosure_type_enum_values_are_title_cased() -> None:
    """EnclosureType values are title-cased (Mammal, Bird, Reptile)."""
    assert EnclosureType.MAMMAL.value == "Mammal"
    assert EnclosureType.BIRD.value == "Bird"
    assert EnclosureType.REPTILE.value == "Reptile"


def test_health_result_enum_has_three_values() -> None:
    """HealthResult enum has HEALTHY, NEED_FOLLOW_UP, CRITICAL."""
    assert HealthResult.HEALTHY.value == "healthy"
    assert HealthResult.NEED_FOLLOW_UP.value == "need_follow_up"
    assert HealthResult.CRITICAL.value == "critical"
