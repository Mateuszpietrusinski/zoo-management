"""Unit tests for AdmissionRecord, HealthCheckRecord, Tour."""

from datetime import date, datetime

from zoo_management.domain.entities import (
    AdmissionRecord,
    HealthCheckRecord,
    HealthResult,
    Tour,
)


def test_admission_record_creation() -> None:
    """AdmissionRecord is created with required fields."""
    rec = AdmissionRecord(
        id="ar-1",
        date=date(2025, 3, 10),
        animal_id="a1",
        enclosure_id="enc-1",
        zookeeper_id="zk-1",
        vet_id="vet-1",
        health_check_record_id="hc-1",
    )
    assert rec.id == "ar-1"
    assert rec.date == date(2025, 3, 10)
    assert rec.animal_id == "a1"
    assert rec.enclosure_id == "enc-1"
    assert rec.zookeeper_id == "zk-1"
    assert rec.vet_id == "vet-1"
    assert rec.health_check_record_id == "hc-1"


def test_admission_record_health_check_record_id_nullable() -> None:
    """AdmissionRecord.health_check_record_id can be None (ADR-027)."""
    rec = AdmissionRecord(
        id="ar-1",
        date=date(2025, 3, 10),
        animal_id="a1",
        enclosure_id="enc-1",
        zookeeper_id=None,
        vet_id=None,
        health_check_record_id=None,
    )
    assert rec.health_check_record_id is None


def test_admission_record_repr_str() -> None:
    """AdmissionRecord has __repr__ and __str__."""
    rec = AdmissionRecord(
        id="ar-1",
        date=date(2025, 3, 10),
        animal_id="a1",
        enclosure_id="enc-1",
        zookeeper_id="zk-1",
        vet_id=None,
        health_check_record_id=None,
    )
    assert "ar-1" in repr(rec)
    assert "ar-1" in str(rec) or "a1" in str(rec)


def test_health_check_record_creation() -> None:
    """HealthCheckRecord is created with required fields."""
    rec = HealthCheckRecord(
        id="hc-1",
        date=date(2025, 3, 10),
        animal_id="a1",
        vet_id="vet-1",
        result=HealthResult.HEALTHY,
        notes="All good",
    )
    assert rec.id == "hc-1"
    assert rec.animal_id == "a1"
    assert rec.vet_id == "vet-1"
    assert rec.result == HealthResult.HEALTHY
    assert rec.notes == "All good"


def test_health_check_record_notes_nullable() -> None:
    """HealthCheckRecord.notes can be None."""
    rec = HealthCheckRecord(
        id="hc-1",
        date=date(2025, 3, 10),
        animal_id="a1",
        vet_id="vet-1",
        result=HealthResult.HEALTHY,
        notes=None,
    )
    assert rec.notes is None


def test_health_check_record_repr_str() -> None:
    """HealthCheckRecord has __repr__ and __str__."""
    rec = HealthCheckRecord(
        id="hc-1",
        date=date(2025, 3, 10),
        animal_id="a1",
        vet_id="vet-1",
        result=HealthResult.HEALTHY,
        notes=None,
    )
    assert "hc-1" in repr(rec)
    assert "hc-1" in str(rec) or "a1" in str(rec)


def test_tour_creation_with_route_and_times() -> None:
    """Tour is created with id, guide_id, route, start_time, end_time."""
    start = datetime(2025, 3, 10, 10, 0)
    end = datetime(2025, 3, 10, 11, 0)
    tour = Tour(
        id="tour-1",
        guide_id="guide-1",
        route=["enc-1", "enc-2"],
        start_time=start,
        end_time=end,
    )
    assert tour.id == "tour-1"
    assert tour.guide_id == "guide-1"
    assert tour.route == ["enc-1", "enc-2"]
    assert tour.start_time == start
    assert tour.end_time == end


def test_tour_is_completed_true_when_end_time_set() -> None:
    """Tour.is_completed is True when end_time is set."""
    start = datetime(2025, 3, 10, 10, 0)
    end = datetime(2025, 3, 10, 11, 0)
    tour = Tour(
        id="tour-1",
        guide_id="guide-1",
        route=[],
        start_time=start,
        end_time=end,
    )
    assert tour.is_completed is True


def test_tour_repr_str() -> None:
    """Tour has __repr__ and __str__."""
    start = datetime(2025, 3, 10, 10, 0)
    end = datetime(2025, 3, 10, 11, 0)
    tour = Tour(
        id="tour-1",
        guide_id="guide-1",
        route=[],
        start_time=start,
        end_time=end,
    )
    assert "tour-1" in repr(tour)
    assert "tour-1" in str(tour) or "guide-1" in str(tour)
