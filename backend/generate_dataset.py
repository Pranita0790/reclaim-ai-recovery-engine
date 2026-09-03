from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

from app.models.case import FailureReason, PaymentStatus


FIELDS = [
    "case_id", "customer_id", "amount", "currency", "payment_status",
    "failure_reason", "failure_count", "customer_attempt_count",
    "days_since_failure", "is_customer_active", "has_valid_payment_method",
    "scenario_labels",
]


def _profile(index: int, randomizer: random.Random) -> dict[str, object]:
    """Sample one intentionally covered evaluation scenario."""

    profile_number = index % 5
    if profile_number == 0:
        amount = round(randomizer.uniform(100, 900), 2)
        failures = randomizer.randint(0, 2)
        days = randomizer.randint(31, 60)
        active, valid = False, False
        status = PaymentStatus.EXPIRED
        reason = randomizer.choice([FailureReason.PAYMENT_METHOD_EXPIRED, FailureReason.UNKNOWN])
    elif profile_number == 1:
        amount = round(randomizer.uniform(500, 9000), 2)
        failures = randomizer.randint(0, 2)
        days = randomizer.randint(0, 7)
        active, valid = True, True
        status = randomizer.choice([PaymentStatus.FAILED, PaymentStatus.RECOVERABLE])
        reason = randomizer.choice([FailureReason.NETWORK_ERROR, FailureReason.INSUFFICIENT_FUNDS])
    elif profile_number == 2:
        amount = round(randomizer.uniform(1000, 10000), 2)
        failures = randomizer.randint(1, 3)
        days = randomizer.randint(1, 14)
        active, valid = True, randomizer.random() < 0.35
        status = randomizer.choice([PaymentStatus.FAILED, PaymentStatus.RECOVERABLE])
        reason = randomizer.choice([FailureReason.CARD_DECLINED, FailureReason.UNKNOWN])
    elif profile_number == 3:
        amount = round(randomizer.uniform(10000, 50000), 2)
        failures = randomizer.randint(0, 2)
        days = randomizer.randint(0, 20)
        active, valid = True, True
        status = PaymentStatus.RECOVERABLE
        reason = randomizer.choice([FailureReason.NETWORK_ERROR, FailureReason.CARD_DECLINED])
    else:
        amount = round(randomizer.uniform(1000, 20000), 2)
        failures = randomizer.randint(3, 8)
        days = randomizer.randint(15, 30)
        active = randomizer.random() < 0.45
        valid = randomizer.random() < 0.55
        status = randomizer.choice([PaymentStatus.FAILED, PaymentStatus.RECOVERABLE])
        reason = randomizer.choice(list(FailureReason))

    return {
        "amount": amount,
        "failure_count": failures,
        "customer_attempt_count": randomizer.randint(0, failures),
        "days_since_failure": days,
        "is_customer_active": active,
        "has_valid_payment_method": valid,
        "payment_status": status.value,
        "failure_reason": reason.value,
    }


def derive_scenarios(record: dict[str, object]) -> list[str]:
    """Derive evaluation labels from case features, never from results."""

    amount = float(record["amount"])
    failures = int(record["failure_count"])
    attempts = int(record["customer_attempt_count"])
    days = int(record["days_since_failure"])
    active = bool(record["is_customer_active"])
    valid = bool(record["has_valid_payment_method"])
    labels: list[str] = []
    if amount < 1000:
        labels.append("LOW_VALUE")
    if amount >= 10000:
        labels.append("HIGH_VALUE")
    if days <= 7:
        labels.append("RECENT_FAILURE")
    if days > 30:
        labels.append("AGED_FAILURE")
    if days > 30 or failures >= 3 or attempts >= 3 or not active or not valid:
        labels.append("POLICY_BLOCKED")
    if valid and days <= 7 and failures < 3:
        labels.append("RETRY_FAVORABLE")
    if active and attempts < 3 and days <= 14:
        labels.append("CONTACT_FAVORABLE")
    if amount >= 10000 and days <= 30:
        labels.append("ESCALATION_FAVORABLE")
    if days > 30 or (not active and not valid) or (failures >= 3 and attempts >= 3):
        labels.append("NO_ACTION_FAVORABLE")
    return labels or ["MIXED"]


def generate_cases(count: int = 1000, seed: int = 42) -> list[dict[str, object]]:
    if count <= 0:
        raise ValueError("count must be greater than zero")
    randomizer = random.Random(seed)
    records: list[dict[str, object]] = []
    for index in range(count):
        record = _profile(index, randomizer)
        record.update({
            "case_id": f"BATCH-{index + 1:06d}",
            "customer_id": f"CUSTOMER-{index + 1:06d}",
            "currency": "INR",
            "scenario_labels": "|".join(derive_scenarios(record)),
        })
        records.append(record)
    return records


def write_cases(path: str | Path, count: int = 1000, seed: int = 42) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(generate_cases(count, seed))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a reproducible recovery evaluation dataset.")
    parser.add_argument("--output", default="data/cases.csv")
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    write_cases(args.output, args.count, args.seed)
    print(f"Generated {args.count} cases at {args.output} with seed {args.seed}.")


if __name__ == "__main__":
    main()
