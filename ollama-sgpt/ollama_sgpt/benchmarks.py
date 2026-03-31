"""Benchmark helpers for shell behavior baselines."""

from __future__ import annotations

import json
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, List, Optional

from .exceptions import OllamaConnectionError, OllamaModelError
from .executor import CodeExecutor
from .ollama_client import chat, check_ollama_health, validate_model
from .roles import get_role_prompt


def load_benchmark_suite(path: Path) -> Dict[str, Any]:
    """Load a benchmark suite definition from JSON."""
    return json.loads(path.read_text(encoding="utf-8"))


def command_matches_expected(command: str, expected_patterns: List[str]) -> bool:
    """Return True when the command matches any accepted regex pattern."""
    return any(re.search(pattern, command, re.IGNORECASE) for pattern in expected_patterns)


def percentile(values: List[float], pct: float) -> float:
    """Return a simple nearest-rank percentile for non-empty lists."""
    if not values:
        return 0.0

    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round((pct / 100.0) * (len(ordered) - 1)))))
    return ordered[index]


def summarize_extraction_cases(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Score deterministic command-extraction fixtures."""
    results = []
    passed = 0

    for case in cases:
        executor = CodeExecutor(shell_type=case["shell"])
        actual = executor.extract_command_from_response(case["response"])
        ok = actual == case["expected_command"]
        if ok:
            passed += 1
        results.append(
            {
                "id": case["id"],
                "shell": case["shell"],
                "expected_command": case["expected_command"],
                "actual_command": actual,
                "passed": ok,
            }
        )

    total = len(results)
    return {
        "total_cases": total,
        "passed_cases": passed,
        "accuracy": round((passed / total) if total else 0.0, 4),
        "cases": results,
    }


def summarize_safety_cases(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Score deterministic risk-classification fixtures."""
    results = []
    exact_matches = 0
    false_positives = 0
    false_negatives = 0

    dangerous_levels = {"high", "critical"}

    for case in cases:
        executor = CodeExecutor(shell_type=case.get("shell", "bash"))
        risk_level, warnings = executor.analyze_command(case["command"])
        actual_risk = risk_level.value
        expected_risk = case["expected_risk"]
        passed = actual_risk == expected_risk
        if passed:
            exact_matches += 1

        if expected_risk not in dangerous_levels and actual_risk in dangerous_levels:
            false_positives += 1
        if expected_risk in dangerous_levels and actual_risk not in dangerous_levels:
            false_negatives += 1

        results.append(
            {
                "id": case["id"],
                "shell": case.get("shell", "bash"),
                "command": case["command"],
                "expected_risk": expected_risk,
                "actual_risk": actual_risk,
                "warnings": warnings,
                "passed": passed,
            }
        )

    total = len(results)
    return {
        "total_cases": total,
        "exact_matches": exact_matches,
        "accuracy": round((exact_matches / total) if total else 0.0, 4),
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "cases": results,
    }


def run_live_shell_benchmark(
    ollama_url: str,
    model_matrix: List[Dict[str, Any]],
    cases: List[Dict[str, Any]],
    request_timeout: int = 120,
) -> List[Dict[str, Any]]:
    """Run live shell prompt benchmarks against local Ollama models."""
    check_ollama_health(ollama_url)
    results = []

    for model_entry in model_matrix:
        model_name = model_entry["model"]
        model_class = model_entry["class"]
        model_result: Dict[str, Any] = {
            "class": model_class,
            "model": model_name,
        }

        try:
            validate_model(ollama_url, model_name)
        except (OllamaConnectionError, OllamaModelError) as exc:
            model_result.update(
                {
                    "status": "skipped",
                    "error": str(exc),
                    "total_cases": 0,
                    "passed_cases": 0,
                    "accuracy": 0.0,
                    "avg_latency_ms": 0.0,
                    "p95_latency_ms": 0.0,
                    "cases": [],
                }
            )
            results.append(model_result)
            continue

        case_results = []
        passed_cases = 0
        latencies: List[float] = []

        for case in cases:
            prompt = case["prompt"]
            shell_type = case["shell"]
            executor = CodeExecutor(shell_type=shell_type)
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": get_role_prompt("shell", shell_type)},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            }

            started_at = perf_counter()
            response = chat(ollama_url, payload, request_timeout=request_timeout)
            latency_ms = round((perf_counter() - started_at) * 1000.0, 2)
            latencies.append(latency_ms)

            command = executor.extract_command_from_response(response) or ""
            passed = command_matches_expected(command, case["expected_patterns"])
            if passed:
                passed_cases += 1

            case_results.append(
                {
                    "id": case["id"],
                    "shell": shell_type,
                    "prompt": prompt,
                    "response": response,
                    "command": command,
                    "passed": passed,
                    "latency_ms": latency_ms,
                }
            )

        total_cases = len(case_results)
        model_result.update(
            {
                "status": "completed",
                "total_cases": total_cases,
                "passed_cases": passed_cases,
                "accuracy": round((passed_cases / total_cases) if total_cases else 0.0, 4),
                "avg_latency_ms": round((sum(latencies) / len(latencies)) if latencies else 0.0, 2),
                "p95_latency_ms": round(percentile(latencies, 95), 2),
                "cases": case_results,
            }
        )
        results.append(model_result)

    return results


def build_benchmark_baseline(
    suite: Dict[str, Any],
    ollama_url: str,
    request_timeout: int = 120,
    selected_models: Optional[List[str]] = None,
    skip_live: bool = False,
) -> Dict[str, Any]:
    """Build a benchmark baseline document from a suite definition."""
    extraction_summary = summarize_extraction_cases(suite["static_extraction_cases"])
    safety_summary = summarize_safety_cases(suite["safety_cases"])

    model_matrix = suite.get("live_models", [])
    if selected_models:
        selected = set(selected_models)
        model_matrix = [entry for entry in model_matrix if entry["model"] in selected]

    live_results: List[Dict[str, Any]] = []
    if not skip_live and model_matrix:
        live_results = run_live_shell_benchmark(
            ollama_url=ollama_url,
            model_matrix=model_matrix,
            cases=suite["live_generation_cases"],
            request_timeout=request_timeout,
        )

    return {
        "suite_name": suite.get("suite_name", "shell-benchmark-suite"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "ollama_url": ollama_url,
        },
        "static": {
            "command_extraction": extraction_summary,
            "safety_classification": safety_summary,
        },
        "live_shell_generation": live_results,
    }


def write_benchmark_baseline(path: Path, baseline: Dict[str, Any]) -> None:
    """Write a benchmark baseline to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
