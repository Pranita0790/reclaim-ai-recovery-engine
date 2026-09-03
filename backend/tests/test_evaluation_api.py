from pathlib import Path

from fastapi.testclient import TestClient

from app.api.evaluation_routes import evaluation_service
from app.main import app


client = TestClient(app)


def test_evaluation_summary_returns_real_benchmark() -> None:
    response = client.get("/api/v1/evaluation/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_size"] == 1000
    assert data["seeds"] == [42, 43, 44, 45, 46]
    assert "RECLAIM Hybrid" in data["strategies"]
    assert data["best_baseline"]
    assert 0 <= data["reclaim_recovery_rate"] <= 1
    assert 0 <= data["reclaim_policy_compliance_rate"] <= 1


def test_strategy_endpoint_returns_detailed_results() -> None:
    response = client.get("/api/v1/evaluation/strategies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    hybrid = next(item for item in data if item["strategy_name"] == "RECLAIM Hybrid")
    assert "case_recovery_rate" in hybrid
    assert "attempt_recovery_rate" in hybrid
    assert "policy_compliance_rate" in hybrid
    assert "action_distribution" in hybrid


def test_multiseed_endpoint_returns_real_variation_summary() -> None:
    response = client.get("/api/v1/evaluation/multiseed")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert all(item["stddev_net_value"] >= 0 for item in data)


def test_scenario_and_strategy_filters() -> None:
    all_scenarios = client.get("/api/v1/evaluation/scenarios")
    filtered = client.get("/api/v1/evaluation/scenarios", params={"strategy": "RECLAIM Hybrid"})
    assert all_scenarios.status_code == 200
    assert filtered.status_code == 200
    assert len(filtered.json()) < len(all_scenarios.json())
    assert all(item["strategy"] == "RECLAIM Hybrid" for item in filtered.json())
    scenario_name = filtered.json()[0]["scenario"]
    cases = client.get("/api/v1/evaluation/cases", params={"strategy": "RECLAIM Hybrid", "scenario": scenario_name, "limit": 3})
    assert cases.status_code == 200
    assert 1 <= len(cases.json()) <= 3
    assert all(item["strategy"] == "RECLAIM Hybrid" and scenario_name in item["scenario_labels"] for item in cases.json())


def test_cases_limit_validation() -> None:
    response = client.get("/api/v1/evaluation/cases", params={"limit": 0})
    assert response.status_code == 422
    response = client.get("/api/v1/evaluation/cases", params={"limit": 2})
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_evaluation_results_are_deterministic() -> None:
    first = client.get("/api/v1/evaluation/summary")
    second = client.get("/api/v1/evaluation/summary")
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()


def test_missing_or_malformed_dataset_returns_http_error(tmp_path: Path, monkeypatch) -> None:
    missing = tmp_path / "missing.csv"
    monkeypatch.setattr(evaluation_service, "dataset_path", missing)
    assert client.get("/api/v1/evaluation/summary").status_code == 422
    malformed = tmp_path / "malformed.csv"
    malformed.write_text("case_id\nCASE-1\n", encoding="utf-8")
    monkeypatch.setattr(evaluation_service, "dataset_path", malformed)
    assert client.get("/api/v1/evaluation/summary").status_code == 422
