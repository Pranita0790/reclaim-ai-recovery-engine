from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.models.case import RecoveryCase


REQUIRED_FIELDS = (
    "case_id",
    "customer_id",
    "amount",
    "currency",
    "payment_status",
    "failure_reason",
    "failure_count",
    "customer_attempt_count",
    "days_since_failure",
    "is_customer_active",
    "has_valid_payment_method",
)


class DatasetValidationError(ValueError):
    """Raised when an evaluation dataset cannot be loaded safely."""


@dataclass(frozen=True)
class EvaluationCase:
    case: RecoveryCase
    scenarios: tuple[str, ...]


def _parse_bool(value: str, field: str, row_number: int) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise DatasetValidationError(
        f"Row {row_number}: {field} must be true or false, got {value!r}."
    )


def _parse_row(row: dict[str, str], row_number: int) -> RecoveryCase:
    missing = [field for field in REQUIRED_FIELDS if not row.get(field, "").strip()]
    if missing:
        raise DatasetValidationError(
            f"Row {row_number}: missing required fields: {', '.join(missing)}."
        )

    try:
        payload: dict[str, Any] = dict(row)
        payload["amount"] = float(row["amount"])
        payload["failure_count"] = int(row["failure_count"])
        payload["customer_attempt_count"] = int(row["customer_attempt_count"])
        payload["days_since_failure"] = int(row["days_since_failure"])
        payload["is_customer_active"] = _parse_bool(
            row["is_customer_active"], "is_customer_active", row_number
        )
        payload["has_valid_payment_method"] = _parse_bool(
            row["has_valid_payment_method"],
            "has_valid_payment_method",
            row_number,
        )
        return RecoveryCase.model_validate(payload)
    except (ValueError, ValidationError) as error:
        raise DatasetValidationError(
            f"Row {row_number}: invalid recovery case: {error}"
        ) from error


def load_cases(path: str | Path) -> list[EvaluationCase]:
    """Load and validate every recovery case in a CSV file."""

    dataset_path = Path(path)
    if not dataset_path.exists():
        raise DatasetValidationError(f"Dataset does not exist: {dataset_path}")

    with dataset_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise DatasetValidationError("Dataset has no CSV header.")

        missing_header_fields = [
            field for field in REQUIRED_FIELDS if field not in reader.fieldnames
        ]
        if missing_header_fields:
            raise DatasetValidationError(
                "Dataset header is missing required fields: "
                + ", ".join(missing_header_fields)
            )

        cases = []
        for index, row in enumerate(reader, start=2):
            case = _parse_row(row, index)
            labels = tuple(label for label in row.get("scenario_labels", "").split("|") if label)
            if not labels:
                raise DatasetValidationError(f"Row {index}: scenario_labels cannot be empty.")
            cases.append(EvaluationCase(case=case, scenarios=labels))

    if not cases:
        raise DatasetValidationError("Dataset contains no recovery cases.")
    return cases
