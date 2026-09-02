from fastapi.testclient import TestClient

from app.main import app
from app.services.audit_repository import AuditRepository


client = TestClient(app)


# --------------------------------------------------
# TEST DATABASE CLEANUP
# --------------------------------------------------

audit_repository = AuditRepository()


def clear_case(case_id: str) -> None:
    """Remove previous persistent events for a test case."""

    audit_repository.delete_case_events(
        case_id
    )


# --------------------------------------------------
# TEST DATA
# --------------------------------------------------

SUCCESSFUL_CASE = {
    "case_id": "API-TEST-001",
    "customer_id": "CUSTOMER-001",
    "amount": 5000,
    "currency": "INR",
    "payment_status": "RECOVERABLE",
    "failure_reason": "NETWORK_ERROR",
    "failure_count": 1,
    "customer_attempt_count": 0,
    "days_since_failure": 1,
    "is_customer_active": True,
    "has_valid_payment_method": True,
    "metadata": {},
}


REJECTED_CASE = {
    "case_id": "API-TEST-002",
    "customer_id": "CUSTOMER-002",
    "amount": 1,
    "currency": "INR",
    "payment_status": "FAILED",
    "failure_reason": "INSUFFICIENT_FUNDS",
    "failure_count": 1,
    "customer_attempt_count": 0,
    "days_since_failure": 0,
    "is_customer_active": True,
    "has_valid_payment_method": True,
    "metadata": {},
}


EXPIRED_CASE = {
    "case_id": "API-TEST-003",
    "customer_id": "CUSTOMER-003",
    "amount": 5000,
    "currency": "INR",
    "payment_status": "EXPIRED",
    "failure_reason": "NETWORK_ERROR",
    "failure_count": 1,
    "customer_attempt_count": 0,
    "days_since_failure": 31,
    "is_customer_active": True,
    "has_valid_payment_method": True,
    "metadata": {},
}


# --------------------------------------------------
# TEST: SUCCESSFUL RECOVERY
# --------------------------------------------------

def test_successful_recovery() -> None:

    clear_case("API-TEST-001")

    response = client.post(
        "/api/v1/recovery/process",
        json=SUCCESSFUL_CASE,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["case_id"] == "API-TEST-001"
    assert data["decision_status"] == "APPROVED"
    assert data["execution_status"] == "SUCCESS"
    assert data["final_state"] == "RECOVERED"

    print("\nSUCCESSFUL RECOVERY")
    print(data)


# --------------------------------------------------
# TEST: REJECTED RECOVERY
# --------------------------------------------------

def test_rejected_recovery() -> None:

    clear_case("API-TEST-002")

    response = client.post(
        "/api/v1/recovery/process",
        json=REJECTED_CASE,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["case_id"] == "API-TEST-002"
    assert data["recommended_action"] == "DO_NOTHING"
    assert data["decision_status"] == "REJECTED"
    assert data["execution_status"] == "SKIPPED"
    assert data["final_state"] == "FAILED"

    print("\nREJECTED RECOVERY")
    print(data)


# --------------------------------------------------
# TEST: EXPIRED RECOVERY CASE
# --------------------------------------------------

def test_expired_recovery_case() -> None:

    clear_case("API-TEST-003")

    response = client.post(
        "/api/v1/recovery/process",
        json=EXPIRED_CASE,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["case_id"] == "API-TEST-003"
    assert data["final_state"] == "EXPIRED"

    print("\nEXPIRED RECOVERY CASE")
    print(data)


# --------------------------------------------------
# TEST: INVALID REQUEST
# --------------------------------------------------

def test_invalid_request() -> None:

    invalid_case = {
        "case_id": "API-TEST-004",
        "customer_id": "CUSTOMER-004",
        "payment_status": "FAILED",
        "failure_reason": "NETWORK_ERROR",
    }

    response = client.post(
        "/api/v1/recovery/process",
        json=invalid_case,
    )

    assert response.status_code == 422

    data = response.json()

    assert "detail" in data

    print("\nINVALID REQUEST")
    print(data)


# --------------------------------------------------
# TEST: BUSINESS VALIDATION ERROR
# --------------------------------------------------

def test_business_validation_error() -> None:

    invalid_business_case = {
        "case_id": "API-TEST-005",
        "customer_id": "CUSTOMER-005",
        "amount": 5000,
        "currency": "INR",
        "payment_status": "RECOVERABLE",
        "failure_reason": "NETWORK_ERROR",
        "failure_count": 1,
        "customer_attempt_count": 2,
        "days_since_failure": 1,
        "is_customer_active": True,
        "has_valid_payment_method": True,
        "metadata": {},
    }

    response = client.post(
        "/api/v1/recovery/process",
        json=invalid_business_case,
    )

    assert response.status_code == 400

    data = response.json()

    assert data["error"] == (
        "BUSINESS_VALIDATION_ERROR"
    )

    assert (
        data["message"]
        == (
            "Customer attempt count cannot exceed "
            "failure count."
        )
    )

    print("\nBUSINESS VALIDATION ERROR")
    print(data)


# --------------------------------------------------
# TEST: CASE AUDIT TRAIL
# --------------------------------------------------

def test_get_case_audit_trail() -> None:

    clear_case("API-TEST-001")

    process_response = client.post(
        "/api/v1/recovery/process",
        json=SUCCESSFUL_CASE,
    )

    assert process_response.status_code == 200

    response = client.get(
        "/api/v1/recovery/API-TEST-001/audit"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["case_id"] == "API-TEST-001"

    assert len(data["events"]) == 5

    event_types = [
        event["event_type"]
        for event in data["events"]
    ]

    assert event_types == [
        "CASE_RECEIVED",
        "POLICY_EVALUATED",
        "DECISION_CREATED",
        "EXECUTION_STARTED",
        "EXECUTION_COMPLETED",
    ]

    decision_event = next(
        event
        for event in data["events"]
        if event["event_type"]
        == "DECISION_CREATED"
    )

    assert (
        "ml_recovery_probability"
        in decision_event["data"]
    )

    assert (
        "final_action_probability"
        in decision_event["data"]
    )

    assert (
        "expected_value"
        in decision_event["data"]
    )

    print("\nCASE AUDIT TRAIL")
    print(data)


# --------------------------------------------------
# TEST: UNKNOWN AUDIT CASE
# --------------------------------------------------

def test_unknown_case_audit_returns_404() -> None:

    clear_case("UNKNOWN-CASE-999")

    response = client.get(
        "/api/v1/recovery/"
        "UNKNOWN-CASE-999/audit"
    )

    assert response.status_code == 404


# --------------------------------------------------
# TEST: GET ALL AUDIT EVENTS
# --------------------------------------------------

def test_get_all_audit_events() -> None:

    response = client.get(
        "/api/v1/recovery/audit"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    assert len(data) > 0

    print("\nALL AUDIT EVENTS")
    print(data)