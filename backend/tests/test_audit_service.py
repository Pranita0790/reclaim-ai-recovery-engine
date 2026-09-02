from app.models.audit import AuditEventType
from app.services.audit_repository import AuditRepository
from app.services.audit_service import AuditService


# ------------------------------------------------------------
# TEST 1: Record audit events
# ------------------------------------------------------------

def test_record_audit_events() -> None:
    audit_service = AuditService()

    case_id = "CASE-001"

    event_1 = audit_service.record_event(
        case_id=case_id,
        event_type=AuditEventType.CASE_RECEIVED,
        message="Recovery case received.",
    )

    event_2 = audit_service.record_event(
        case_id=case_id,
        event_type=AuditEventType.BASELINE_ESTIMATED,
        message="Baseline success probabilities estimated.",
        data={
            "retry_probability": 0.79,
            "contact_probability": 0.53,
        },
    )

    event_3 = audit_service.record_event(
        case_id=case_id,
        event_type=AuditEventType.DECISION_CREATED,
        message="Recovery decision created.",
        data={
            "recommended_action": "RETRY_PAYMENT",
            "confidence": 0.79,
        },
    )

    assert event_1.event_type is AuditEventType.CASE_RECEIVED
    assert event_2.event_type is AuditEventType.BASELINE_ESTIMATED
    assert event_3.event_type is AuditEventType.DECISION_CREATED


# ------------------------------------------------------------
# TEST 2: Get events for a case
# ------------------------------------------------------------

def test_get_case_events() -> None:
    audit_service = AuditService()

    case_id = "CASE-001"

    audit_service.record_event(
        case_id=case_id,
        event_type=AuditEventType.CASE_RECEIVED,
        message="Recovery case received.",
    )

    audit_service.record_event(
        case_id=case_id,
        event_type=AuditEventType.BASELINE_ESTIMATED,
        message="Baseline success probabilities estimated.",
    )

    audit_service.record_event(
        case_id=case_id,
        event_type=AuditEventType.DECISION_CREATED,
        message="Recovery decision created.",
    )

    case_events = audit_service.get_case_events(
        case_id
    )

    assert len(case_events) == 3

    assert (
        case_events[0].event_type
        is AuditEventType.CASE_RECEIVED
    )

    assert (
        case_events[1].event_type
        is AuditEventType.BASELINE_ESTIMATED
    )

    assert (
        case_events[2].event_type
        is AuditEventType.DECISION_CREATED
    )


# ------------------------------------------------------------
# TEST 3: Different case isolation
# ------------------------------------------------------------

def test_case_event_isolation() -> None:
    audit_service = AuditService()

    audit_service.record_event(
        case_id="CASE-001",
        event_type=AuditEventType.CASE_RECEIVED,
        message="First recovery case received.",
    )

    audit_service.record_event(
        case_id="CASE-001",
        event_type=AuditEventType.DECISION_CREATED,
        message="First recovery decision created.",
    )

    audit_service.record_event(
        case_id="CASE-002",
        event_type=AuditEventType.CASE_RECEIVED,
        message="Second recovery case received.",
    )

    case_1_events = audit_service.get_case_events(
        "CASE-001"
    )

    case_2_events = audit_service.get_case_events(
        "CASE-002"
    )

    assert len(case_1_events) == 2
    assert len(case_2_events) == 1

    assert all(
        event.case_id == "CASE-001"
        for event in case_1_events
    )

    assert all(
        event.case_id == "CASE-002"
        for event in case_2_events
    )


# ------------------------------------------------------------
# TEST 4: Clear case events
# ------------------------------------------------------------

def test_clear_case_events() -> None:
    audit_service = AuditService()

    audit_service.record_event(
        case_id="CASE-001",
        event_type=AuditEventType.CASE_RECEIVED,
        message="First recovery case received.",
    )

    audit_service.record_event(
        case_id="CASE-001",
        event_type=AuditEventType.DECISION_CREATED,
        message="Recovery decision created.",
    )

    audit_service.record_event(
        case_id="CASE-002",
        event_type=AuditEventType.CASE_RECEIVED,
        message="Second recovery case received.",
    )

    audit_service.clear_case_events(
        "CASE-001"
    )

    case_1_events = audit_service.get_case_events(
        "CASE-001"
    )

    case_2_events = audit_service.get_case_events(
        "CASE-002"
    )

    assert len(case_1_events) == 0
    assert len(case_2_events) == 1


# ------------------------------------------------------------
# TEST 5: SQLite repository persists events
# ------------------------------------------------------------

def test_audit_repository_persists_events(
    tmp_path,
) -> None:
    database_path = (
        tmp_path / "persistent_reclaim.db"
    )

    repository = AuditRepository(
        database_path=database_path,
    )

    audit_service = AuditService()

    event = audit_service.record_event(
        case_id="PERSIST-CASE-001",
        event_type=AuditEventType.CASE_RECEIVED,
        message="Persistent recovery case received.",
        data={
            "source": "test",
        },
    )

    repository.save_event(
        event
    )

    stored_events = (
        repository.get_case_events(
            "PERSIST-CASE-001"
        )
    )

    assert len(stored_events) == 1

    stored_event = stored_events[0]

    assert (
        stored_event.event_id
        == event.event_id
    )

    assert (
        stored_event.case_id
        == "PERSIST-CASE-001"
    )

    assert (
        stored_event.event_type
        is AuditEventType.CASE_RECEIVED
    )

    assert (
        stored_event.message
        == "Persistent recovery case received."
    )

    assert stored_event.data == {
        "source": "test",
    }


# ------------------------------------------------------------
# TEST 6: SQLite repository keeps cases isolated
# ------------------------------------------------------------

def test_audit_repository_case_isolation(
    tmp_path,
) -> None:
    database_path = (
        tmp_path / "isolation_reclaim.db"
    )

    repository = AuditRepository(
        database_path=database_path,
    )

    audit_service = AuditService()

    event_1 = audit_service.record_event(
        case_id="PERSIST-CASE-001",
        event_type=AuditEventType.CASE_RECEIVED,
        message="First persistent case received.",
    )

    event_2 = audit_service.record_event(
        case_id="PERSIST-CASE-001",
        event_type=AuditEventType.DECISION_CREATED,
        message="First persistent decision created.",
    )

    event_3 = audit_service.record_event(
        case_id="PERSIST-CASE-002",
        event_type=AuditEventType.CASE_RECEIVED,
        message="Second persistent case received.",
    )

    repository.save_event(event_1)
    repository.save_event(event_2)
    repository.save_event(event_3)

    first_case_events = (
        repository.get_case_events(
            "PERSIST-CASE-001"
        )
    )

    second_case_events = (
        repository.get_case_events(
            "PERSIST-CASE-002"
        )
    )

    assert len(first_case_events) == 2
    assert len(second_case_events) == 1

    assert all(
        event.case_id
        == "PERSIST-CASE-001"
        for event in first_case_events
    )

    assert all(
        event.case_id
        == "PERSIST-CASE-002"
        for event in second_case_events
    )


# ------------------------------------------------------------
# TEST 7: SQLite repository deletes case events
# ------------------------------------------------------------

def test_audit_repository_delete_case_events(
    tmp_path,
) -> None:
    database_path = (
        tmp_path / "delete_reclaim.db"
    )

    repository = AuditRepository(
        database_path=database_path,
    )

    audit_service = AuditService()

    event_1 = audit_service.record_event(
        case_id="DELETE-CASE-001",
        event_type=AuditEventType.CASE_RECEIVED,
        message="Case to delete.",
    )

    event_2 = audit_service.record_event(
        case_id="KEEP-CASE-001",
        event_type=AuditEventType.CASE_RECEIVED,
        message="Case to keep.",
    )

    repository.save_event(event_1)
    repository.save_event(event_2)

    repository.delete_case_events(
        "DELETE-CASE-001"
    )

    deleted_case_events = (
        repository.get_case_events(
            "DELETE-CASE-001"
        )
    )

    remaining_case_events = (
        repository.get_case_events(
            "KEEP-CASE-001"
        )
    )

    assert len(deleted_case_events) == 0
    assert len(remaining_case_events) == 1


# ------------------------------------------------------------
# TEST 8: SQLite repository returns all events
# ------------------------------------------------------------

def test_audit_repository_get_all_events(
    tmp_path,
) -> None:
    database_path = (
        tmp_path / "all_events_reclaim.db"
    )

    repository = AuditRepository(
        database_path=database_path,
    )

    audit_service = AuditService()

    event_1 = audit_service.record_event(
        case_id="ALL-CASE-001",
        event_type=AuditEventType.CASE_RECEIVED,
        message="First event.",
    )

    event_2 = audit_service.record_event(
        case_id="ALL-CASE-002",
        event_type=AuditEventType.DECISION_CREATED,
        message="Second event.",
    )

    repository.save_event(event_1)
    repository.save_event(event_2)

    all_events = (
        repository.get_all_events()
    )

    assert len(all_events) == 2

    event_ids = {
        event.event_id
        for event in all_events
    }

    assert event_1.event_id in event_ids
    assert event_2.event_id in event_ids