from app.models.audit import AuditEventType
from app.services.audit_repository import AuditRepository
from app.services.audit_service import AuditService


def test_audit_event_is_persisted(
    tmp_path,
) -> None:
    database_path = (
        tmp_path / "reclaim_test.db"
    )

    repository = AuditRepository(
        database_path
    )

    audit_service = AuditService(
        repository=repository
    )

    event = audit_service.record_event(
        case_id="PERSIST-001",
        event_type=AuditEventType.CASE_RECEIVED,
        message="Recovery case received.",
    )

    stored_events = repository.get_case_events(
        "PERSIST-001"
    )

    assert len(stored_events) == 1
    assert stored_events[0].event_id == event.event_id
    assert (
        stored_events[0].event_type
        is AuditEventType.CASE_RECEIVED
    )


def test_audit_events_survive_new_service_instance(
    tmp_path,
) -> None:
    database_path = (
        tmp_path / "reclaim_test.db"
    )

    repository = AuditRepository(
        database_path
    )

    first_service = AuditService(
        repository=repository
    )

    first_service.record_event(
        case_id="PERSIST-002",
        event_type=AuditEventType.CASE_RECEIVED,
        message="Recovery case received.",
    )

    # Simulate application/service restart.
    second_repository = AuditRepository(
        database_path
    )

    second_service = AuditService(
        repository=second_repository
    )

    events = second_service.get_case_events(
        "PERSIST-002"
    )

    assert len(events) == 1
    assert (
        events[0].message
        == "Recovery case received."
    )


def test_persistent_case_event_isolation(
    tmp_path,
) -> None:
    database_path = (
        tmp_path / "reclaim_test.db"
    )

    repository = AuditRepository(
        database_path
    )

    audit_service = AuditService(
        repository=repository
    )

    audit_service.record_event(
        case_id="PERSIST-003",
        event_type=AuditEventType.CASE_RECEIVED,
        message="First case received.",
    )

    audit_service.record_event(
        case_id="PERSIST-003",
        event_type=AuditEventType.DECISION_CREATED,
        message="First decision created.",
    )

    audit_service.record_event(
        case_id="PERSIST-004",
        event_type=AuditEventType.CASE_RECEIVED,
        message="Second case received.",
    )

    first_case_events = (
        audit_service.get_case_events(
            "PERSIST-003"
        )
    )

    second_case_events = (
        audit_service.get_case_events(
            "PERSIST-004"
        )
    )

    assert len(first_case_events) == 2
    assert len(second_case_events) == 1


def test_clear_events_removes_persistent_events(
    tmp_path,
) -> None:
    database_path = (
        tmp_path / "reclaim_test.db"
    )

    repository = AuditRepository(
        database_path
    )

    audit_service = AuditService(
        repository=repository
    )

    audit_service.record_event(
        case_id="PERSIST-005",
        event_type=AuditEventType.CASE_RECEIVED,
        message="Recovery case received.",
    )

    audit_service.record_event(
        case_id="PERSIST-006",
        event_type=AuditEventType.CASE_RECEIVED,
        message="Another recovery case received.",
    )

    audit_service.clear_case_events(
        "PERSIST-005"
    )

    cleared_events = (
        repository.get_case_events(
            "PERSIST-005"
        )
    )

    remaining_events = (
        repository.get_case_events(
            "PERSIST-006"
        )
    )

    assert len(cleared_events) == 0
    assert len(remaining_events) == 1