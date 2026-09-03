from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.models.decision import RecoveryAction
from app.services.action_evaluator import ActionEvaluator
from app.services.evaluation_service import EvaluationService


client = TestClient(app)


def test_replay_returns_real_case_context_and_all_actions() -> None:
    case_id = Path("data/cases.csv").read_text(encoding="utf-8").splitlines()[1].split(",")[0]
    response = client.get(f"/api/v1/evaluation/replay/{case_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["case"]["case_id"] == case_id
    assert data["strategy"] == "RECLAIM Hybrid"
    assert data["seed"] == 42
    assert len(data["candidates"]) == len(RecoveryAction)
    assert {candidate["action"] for candidate in data["candidates"]} == {action.value for action in RecoveryAction}
    assert sum(candidate["is_selected"] for candidate in data["candidates"]) == 1
    assert data["decision"]["selected_action"] in {action.value for action in RecoveryAction}
    assert data["regret"] >= 0
    assert data["best_realized_action"] in {action.value for action in RecoveryAction}


def test_replay_candidate_estimates_match_existing_evaluator() -> None:
    service = EvaluationService()
    evaluation_case = service.cases()[0]
    response = client.get(f"/api/v1/evaluation/replay/{evaluation_case.case.case_id}")
    assert response.status_code == 200
    candidates = {candidate["action"]: candidate for candidate in response.json()["candidates"]}
    scores = ActionEvaluator().evaluate_all(evaluation_case.case)
    for score in scores:
        candidate = candidates[score.action.value]
        assert candidate["expected_recovery"] == score.expected_recovery
        assert candidate["expected_value"] == score.expected_value
        assert candidate["success_probability"] == score.success_probability
        expected_allowed = score.is_allowed or score.action is RecoveryAction.DO_NOTHING
        assert candidate["is_allowed"] == expected_allowed


def test_replay_blocked_action_has_no_realized_value_or_cost() -> None:
    service = EvaluationService()
    blocked_case = next(
        item for item in service.cases()
        if not item.case.has_valid_payment_method
        or item.case.days_since_failure > 30
        or item.case.amount < 1000
    )
    response = client.get(f"/api/v1/evaluation/replay/{blocked_case.case.case_id}")
    assert response.status_code == 200
    blocked = [candidate for candidate in response.json()["candidates"] if not candidate["is_allowed"]]
    assert blocked
    assert all(
        candidate["recovered"] is False
        and candidate["recovered_amount"] == 0
        and candidate["realized_net_value"] == 0
        and candidate["action_cost"] == 0
        for candidate in blocked
    )


def test_replay_unknown_case_and_invalid_seed() -> None:
    assert client.get("/api/v1/evaluation/replay/DOES-NOT-EXIST").status_code == 404
    case_id = EvaluationService().cases()[0].case.case_id
    assert client.get(f"/api/v1/evaluation/replay/{case_id}?seed=-1").status_code == 422


def test_replay_is_deterministic_and_seeded() -> None:
    cases = EvaluationService().cases()[:20]
    case_id = cases[0].case.case_id
    first = client.get(f"/api/v1/evaluation/replay/{case_id}?seed=42")
    second = client.get(f"/api/v1/evaluation/replay/{case_id}?seed=42")
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    same_results = [
        client.get(f"/api/v1/evaluation/replay/{case.case.case_id}?seed=42").json()
        for case in cases
    ]
    different_results = [
        client.get(f"/api/v1/evaluation/replay/{case.case.case_id}?seed=43").json()
        for case in cases
    ]
    assert any(
        any(left["recovered"] != right["recovered"] for left, right in zip(first_result["candidates"], second_result["candidates"]))
        for first_result, second_result in zip(same_results, different_results)
    )


def test_replay_selected_action_uses_decision_engine() -> None:
    service = EvaluationService()
    evaluation_case = service.cases()[0]
    response = client.get(f"/api/v1/evaluation/replay/{evaluation_case.case.case_id}")
    decision = service.get_replay(evaluation_case.case.case_id)
    assert response.json()["decision"]["selected_action"] == decision.decision.selected_action.value
