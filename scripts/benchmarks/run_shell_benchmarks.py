"""Run the v0.3 shell benchmark suite and write a baseline JSON file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = REPO_ROOT / "ollama-sgpt"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from ollama_sgpt.benchmarks import (  # noqa: E402
    build_benchmark_baseline,
    load_benchmark_suite,
    write_benchmark_baseline,
)


DEFAULT_SUITE = REPO_ROOT / "benchmarks" / "shell_suite.json"
DEFAULT_OUTPUT = REPO_ROOT / "benchmarks" / "baselines" / "v0.3-shell-baseline.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run shell benchmark fixtures and optional live Ollama shell-generation benchmarks."
    )
    parser.add_argument(
        "--suite",
        default=str(DEFAULT_SUITE),
        help="Path to the benchmark suite JSON file.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Path to write the benchmark baseline JSON output.",
    )
    parser.add_argument(
        "--ollama-url",
        default="http://localhost:11434/api/chat",
        help="Ollama chat endpoint to use for live benchmarks.",
    )
    parser.add_argument(
        "--request-timeout",
        type=int,
        default=120,
        help="Request timeout for live benchmark calls.",
    )
    parser.add_argument(
        "--models",
        default="",
        help="Comma-separated model names to benchmark instead of the suite default matrix.",
    )
    parser.add_argument(
        "--skip-live",
        action="store_true",
        help="Run only deterministic runtime benchmarks and skip live model calls.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    suite_path = Path(args.suite)
    output_path = Path(args.output)
    selected_models = [item.strip() for item in args.models.split(",") if item.strip()]

    suite = load_benchmark_suite(suite_path)
    baseline = build_benchmark_baseline(
        suite=suite,
        ollama_url=args.ollama_url,
        request_timeout=args.request_timeout,
        selected_models=selected_models or None,
        skip_live=args.skip_live,
    )
    write_benchmark_baseline(output_path, baseline)

    extraction = baseline["static"]["command_extraction"]
    safety = baseline["static"]["safety_classification"]
    print(f"Wrote benchmark baseline to {output_path}")
    print(
        f"Static extraction: {extraction['passed_cases']}/{extraction['total_cases']} "
        f"({extraction['accuracy']:.2%})"
    )
    print(
        f"Static safety: {safety['exact_matches']}/{safety['total_cases']} "
        f"({safety['accuracy']:.2%}), false positives={safety['false_positives']}, "
        f"false negatives={safety['false_negatives']}"
    )

    for result in baseline["live_shell_generation"]:
        status = result["status"]
        if status != "completed":
            print(f"Live {result['class']} / {result['model']}: skipped ({result['error']})")
            continue
        print(
            f"Live {result['class']} / {result['model']}: "
            f"{result['passed_cases']}/{result['total_cases']} "
            f"({result['accuracy']:.2%}), avg latency={result['avg_latency_ms']:.2f} ms, "
            f"p95 latency={result['p95_latency_ms']:.2f} ms"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
