from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.evaluation.dataset_loader import load_cases
from app.evaluation.runner import EvaluationResult, EvaluationRunner, MultiSeedEvaluationResult
from app.evaluation.strategies import (
    AlwaysContactStrategy,
    AlwaysEscalateStrategy,
    AlwaysRetryStrategy,
    DoNothingStrategy,
    ReclaimHybridStrategy,
)


STRATEGY_FACTORIES = {
    "hybrid": ReclaimHybridStrategy,
    "retry": AlwaysRetryStrategy,
    "contact": AlwaysContactStrategy,
    "escalate": AlwaysEscalateStrategy,
    "nothing": DoNothingStrategy,
}


def parse_strategies(value: str):
    names = [name.strip().lower() for name in value.split(",") if name.strip()]
    unknown = [name for name in names if name not in STRATEGY_FACTORIES]
    if unknown:
        raise argparse.ArgumentTypeError(f"Unknown strategies: {', '.join(unknown)}.")
    if not names:
        raise argparse.ArgumentTypeError("At least one strategy is required.")
    return [STRATEGY_FACTORIES[name]() for name in names]


def parse_seeds(value: str) -> list[int]:
    try:
        seeds = [int(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as error:
        raise argparse.ArgumentTypeError("Seeds must be comma-separated integers.") from error
    if not seeds:
        raise argparse.ArgumentTypeError("At least one seed is required.")
    return seeds


def print_single_summary(result: EvaluationResult) -> None:
    print("RECLAIM BATCH EVALUATION")
    print(f"Cases: {result.dataset_size}")
    print(f"Seed: {result.seed}\n")
    print(f"{'Strategy':<20} {'Case Recovery':>14} {'Attempt Rate':>13} {'Recovered INR':>16} {'Net Value':>14} {'Regret':>12}")
    for metrics in result.strategy_results.values():
        print(f"{metrics.strategy_name:<20} {metrics.case_recovery_rate:>13.2%} {metrics.attempt_rate:>12.2%} {metrics.total_recovered_amount:>16,.2f} {metrics.total_net_value:>14,.2f} {metrics.total_regret:>12,.2f}")
    if result.best_baseline_strategy:
        print(f"\nBest baseline: {result.best_baseline_strategy}")
        print(f"Incremental recovered amount: {result.incremental_recovered_amount:,.2f}")
        print(f"Incremental net value: {result.incremental_net_value:,.2f}")


def print_multi_summary(result: MultiSeedEvaluationResult) -> None:
    print("RECLAIM MULTI-SEED BATCH EVALUATION")
    print(f"Cases: {result.dataset_size}")
    print(f"Seeds: {', '.join(str(seed) for seed in result.seeds)}\n")
    print(f"{'Strategy':<20} {'Mean Recovery':>14} {'Mean Recovered':>16} {'Mean Net Value':>16} {'Mean Regret':>14} {'Net Std Dev':>14}")
    for metrics in result.strategy_results.values():
        print(f"{metrics.strategy_name:<20} {metrics.mean_case_recovery_rate:>13.2%} {metrics.mean_recovered_amount:>16,.2f} {metrics.mean_net_value:>16,.2f} {metrics.mean_regret:>14,.2f} {metrics.stddev_net_value:>14,.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate recovery strategies against a CSV dataset.")
    parser.add_argument("--input", default="data/cases.csv", help="Input recovery-case CSV path.")
    parser.add_argument("--seed", type=int, default=None, help="Single outcome simulation seed.")
    parser.add_argument("--seeds", type=parse_seeds, default=None, help="Comma-separated outcome simulation seeds.")
    parser.add_argument("--strategies", type=parse_strategies, default=None, help="Comma-separated names: hybrid,retry,contact,escalate,nothing.")
    parser.add_argument("--output", help="Optional JSON output path.")
    args = parser.parse_args()
    if args.seed is not None and args.seeds is not None:
        parser.error("Use either --seed or --seeds, not both.")
    seeds = args.seeds or [args.seed if args.seed is not None else 42]
    cases = load_cases(args.input)
    runner = EvaluationRunner(seed=seeds[0], strategies=args.strategies)
    result = runner.run(cases) if len(seeds) == 1 else runner.run_many(cases, seeds)
    if isinstance(result, EvaluationResult):
        print_single_summary(result)
    else:
        print_multi_summary(result)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
        print(f"\nWrote structured results to {output_path}")


if __name__ == "__main__":
    main()
